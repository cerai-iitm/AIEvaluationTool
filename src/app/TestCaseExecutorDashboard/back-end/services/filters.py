import sys
import os
from fastapi import HTTPException
from schemas import AllFiltersResponse, FilterResponse
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def get_all_filters_service(db) -> AllFiltersResponse:
    try:
        return AllFiltersResponse(
            domains=[
                FilterResponse(filter_name=d.name)
                for d in db.domains
            ],
            languages=[
                FilterResponse(filter_name=l.name)
                for l in db.languages
            ],
            targets=[
                FilterResponse(
                    filter_name=t.target_name,
                    extra_info=t.target_type
                )
                for t in db.targets
            ],
            statuses=[
                FilterResponse(filter_name="COMPLETED"),
                FilterResponse(filter_name="RUNNING"),
                FilterResponse(filter_name="FAILED"),
            ],
            plans=[
                FilterResponse(filter_name=p.plan_name)
                for p in db.plans
            ],
            metrics=[
                FilterResponse(filter_name=m.metric_name)
                for m in db.metrics
            ],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        