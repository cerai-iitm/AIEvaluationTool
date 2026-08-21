from datetime import datetime
from fastapi import HTTPException
from lib.strategy.utils_new import OllamaConnect
from rich.console import Console
from rich.table import Table
import json
from configuration.paths import PROJECT_ROOT as project_root
import os
from lib.strategy.utils_new import EvaluationReport
from fastapi.responses import FileResponse

def get_report_service(run_name: str, db):
    run = db.get_run_by_name(run_name=run_name)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=f"Run not completed. Current status: {run.status}"
        )
    run_details = db.get_all_run_details_by_run_name(run_name=run.run_name)
    if not run_details:
        raise HTTPException(status_code=404, detail="Run Details not found")  
    score_card = {}
    for detail in run_details:
        conversation = db.get_conversation_by_id(conversation_id=detail.conversation_id)
        if not conversation:
            print(f"Conversation with ID '{detail.conversation_id}' not found in run '{run.run_name}'.")
            continue
        if not conversation.evaluation_ts or conversation.evaluation_score == None:
            print(f"Conversation with ID '{detail.conversation_id}' in run '{run.run_name}' has not been evaluated yet. Skipping.")
            continue
        
        if detail.plan_name not in score_card:
            score_card[detail.plan_name] = {}

        if detail.metric_name not in score_card[detail.plan_name]:
            score_card[detail.plan_name][detail.metric_name] = {"Testcases":{}}

        # capture the score computed for the testcase.
        score_card[detail.plan_name][detail.metric_name]["Testcases"][
            detail.testcase_name
        ] = conversation.evaluation_score

        score_card[detail.plan_name][detail.metric_name].setdefault(
            "Evaluation_Reason", {}
        )[detail.testcase_name] = conversation.evaluation_reason
    
      

    real_plans = [p for p in score_card if p != "PlanSummary"]
    multi_plan = len(real_plans) > 1

    for plan_name, metrics in score_card.items():
        if plan_name == "PlanSummary":
            continue

        for metric_name, metric_data in metrics.items():

            scores = list(metric_data.get("Testcases", {}).values())
            reasons = list(metric_data.get("Evaluation_Reason", {}).values())

            if not scores:
                continue

            metric_score = round(sum(scores) / len(scores), 2)

            metric_summary = OllamaConnect.get_metric_summary(
                metric_name,
                scores=scores,
                reasons=reasons
            )

            metric_data.update({
                "metric_summary": metric_summary,
                "metric_score": metric_score
            })

    # ------------------------------------------------------------
    # SECOND PASS: Plan-level summaries
    # ------------------------------------------------------------

    # initialize the plan_summary for each plan, we will update it in place in the score_card
    plan_summary = ""
    for plan_name, metrics in score_card.items():
        if plan_name == "PlanSummary":
            continue

        plan_summary = OllamaConnect.get_single_plan_summary(plan_name, metrics)

        for metric_data in metrics.values():
            metric_data["plan_summary"] = plan_summary   

    # ------------------------------------------------------------
    # THIRD PASS: Run-level summary (after plans exist)
    # ------------------------------------------------------------
    run_summary = OllamaConnect.get_run_summary(score_card) if multi_plan else ""

    for plan_name, metrics in score_card.items():
        if plan_name == "PlanSummary":
            continue

        for metric_data in metrics.values():
            metric_data["run_summary"] = run_summary             
    # ------------------------------------------------------------
    # TABLE RENDERING
    # ------------------------------------------------------------
    table = Table(title=f"Response Analysis Report for Run '{run.run_name}'")
    table.add_column("Plan Name", style="cyan", no_wrap=True)
    table.add_column("Metric Name", style="magenta")
    table.add_column("Score (0-1)", style="green")
    table.add_column("Metric Summary", style="blue")
    table.add_column("Plan Summary", style="yellow")

    if multi_plan:
        table.add_column("Run Summary", style="blue")

    run_written = False

    for plan_name, metrics in score_card.items():
        if plan_name == "PlanSummary":
            continue

        plan_written = False

        for metric_name, metric_data in metrics.items():

            if "metric_summary" not in metric_data:
                continue

            row = [
                plan_name,
                metric_name,
                str(metric_data["metric_score"]),
                metric_data["metric_summary"],
                metric_data["plan_summary"] if not plan_written else ""
            ]

            if multi_plan:
                row.append(metric_data["run_summary"] if not run_written else "")

            table.add_row(*row)

            plan_written = True
            run_written = True


    print(json.dumps(score_card, indent=4))
    Console().print(table)

    reports_folder = os.path.join(project_root, "reports")
    os.makedirs(reports_folder, exist_ok=True)

    # run = db.get_run_by_name(run_name=args.run_name)
    # if not run:
    #     logger.error(f"Run with name '{args.run_name}' not found.")
    #     return
    
    # target_name = getattr(run, "target")
    # run_name = getattr(run, "run_name")
    # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # # Also save the scrore_card as a JSON for reference.
    # json_path = os.path.join(reports_folder, f"AI_Evaluation_Report_{target_name}_{run_name}.json")
    # with open(json_path, "w") as json_file:
    #     json.dump(score_card, json_file, indent=4)

    # total_testcases = sum(
    #     len(m.get("Testcases", {}))
    #     for metrics in score_card.values()
    #     for m in metrics.values()
    # )

    # if not args.get_report:
    #     logger.info("Report generation skipped as per the argument. Use --get-report or -R flag to generate the PDF report.")
    #     return

    target_name = getattr(run, "target")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    json_path = os.path.join(reports_folder, f"AI_Evaluation_Report_{target_name}_{run_name}.json")
    with open(json_path, "w") as json_file:
        json.dump(score_card, json_file, indent=4)
    total_testcases = sum(
        len(m.get("Testcases", {}))
        for metrics in score_card.values()
        for m in metrics.values()
    )
    report_generator = EvaluationReport()
    headers, rows = report_generator.scorecard_to_table(score_card)
    output_file = os.path.join(
        reports_folder,
        f"AI_Evaluation_Report_{target_name}_{run_name}.pdf"
    )
    filename = report_generator.create_report(
        target_name=target_name,
        run_name=run_name,
        timestamp=timestamp,
        total_testcases=total_testcases,
        run_summary=run_summary,
        headers=headers,
        rows=rows,
        score_card=score_card,
        output_file=output_file,
    )
    return FileResponse(
        path=os.path.join(
            reports_folder,
            f"AI_Evaluation_Report_{target_name}_{run_name}.pdf"
        ),
        media_type='application/pdf',
        filename=f"AI_Evaluation_Report_{target_name}_{run_name}.pdf"
    )