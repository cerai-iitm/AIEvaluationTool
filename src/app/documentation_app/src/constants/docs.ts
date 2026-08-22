export interface DocEntry {
  title: string;
  navTitle?: string;
  path: string;
  sectionId: DocSectionId;
  url: string;
  githubUrl: string;
}

export interface DocSection {
  id: DocSectionId;
  title: string;
  docIds: DocId[];
}

const GITHUB_OWNER = 'cerai-iitm';
const GITHUB_REPO = 'AIEvaluationTool';
const GITHUB_BRANCH = 'main';
const GITHUB_DOCS_PATH = 'docs';

export type DocSectionId =
  | 'overview'
  | 'docker-setup'
  | 'cli'
  | 'ui'
  | 'pqet';

function buildRawRepositoryUrl(repoPath: string) {
  return `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/${GITHUB_BRANCH}/${repoPath}`;
}

function buildGithubRepositoryUrl(repoPath: string) {
  return `https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/${repoPath}`;
}

function buildRawDocUrl(path: string) {
  return buildRawRepositoryUrl(`${GITHUB_DOCS_PATH}/${path}`);
}

function buildGithubDocUrl(path: string) {
  return buildGithubRepositoryUrl(`${GITHUB_DOCS_PATH}/${path}`);
}

const docsConfig = {
  'overview-home': {
    title: 'Overview',
    navTitle: 'Introduction',
    path: 'overview/index.md',
    sectionId: 'overview',
    url: buildRawDocUrl('overview/index.md'),
    githubUrl: buildGithubDocUrl('overview/index.md'),
  },
  'overview-ai-evaluation-tool': {
    title: 'AI Evaluation Tool',
    path: 'overview/aievaluation_tool.md',
    sectionId: 'overview',
    url: buildRawDocUrl('overview/aievaluation_tool.md'),
    githubUrl: buildGithubDocUrl('overview/aievaluation_tool.md'),
  },
  'overview-docker-run': {
    title: 'Docker Run',
    path: 'overview/docker_run.md',
    sectionId: 'overview',
    url: buildRawDocUrl('overview/docker_run.md'),
    githubUrl: buildGithubDocUrl('overview/docker_run.md'),
  },
  'overview-tdms': {
    title: 'TDMS',
    path: 'overview/tdms.md',
    sectionId: 'overview',
    url: buildRawDocUrl('overview/tdms.md'),
    githubUrl: buildGithubDocUrl('overview/tdms.md'),
  },
  'overview-pqet': {
    title: 'PQET',
    path: 'overview/pqet.md',
    sectionId: 'overview',
    url: buildRawDocUrl('overview/pqet.md'),
    githubUrl: buildGithubDocUrl('overview/pqet.md'),
  },
  'docker-setup-home': {
    title: 'Docker Setup',
    navTitle: 'Overview',
    path: 'docker_setup/index.md',
    sectionId: 'docker-setup',
    url: buildRawDocUrl('docker_setup/index.md'),
    githubUrl: buildGithubDocUrl('docker_setup/index.md'),
  },
  'docker-setup-config': {
    title: 'Setup And Configuration',
    navTitle: 'Setup',
    path: 'docker_setup/setup_and_configuration.md',
    sectionId: 'docker-setup',
    url: buildRawDocUrl('docker_setup/setup_and_configuration.md'),
    githubUrl: buildGithubDocUrl('docker_setup/setup_and_configuration.md'),
  },
  'docker-setup-gpu': {
    title: 'GPU Setup',
    path: 'docker_setup/gpu_setup.md',
    sectionId: 'docker-setup',
    url: buildRawDocUrl('docker_setup/gpu_setup.md'),
    githubUrl: buildGithubDocUrl('docker_setup/gpu_setup.md'),
  },
  'docker-setup-run-ui': {
    title: 'Docker Run UI',
    navTitle: 'Run UI',
    path: 'docker_setup/docker_run_ui.md',
    sectionId: 'docker-setup',
    url: buildRawDocUrl('docker_setup/docker_run_ui.md'),
    githubUrl: buildGithubDocUrl('docker_setup/docker_run_ui.md'),
  },
  'docker-setup-run': {
    title: 'Docker Run CLI',
    navTitle: 'Run CLI',
    path: 'docker_setup/docker_run.md',
    sectionId: 'docker-setup',
    url: buildRawDocUrl('docker_setup/docker_run.md'),
    githubUrl: buildGithubDocUrl('docker_setup/docker_run.md'),
  },
  'cli-home': {
    title: 'AI Evaluation Tool CLI',
    navTitle: 'Overview',
    path: 'cli/index.md',
    sectionId: 'cli',
    url: buildRawDocUrl('cli/index.md'),
    githubUrl: buildGithubDocUrl('cli/index.md'),
  },
  'cli-initial-setup': {
    title: 'Initial Setup And Configuration',
    navTitle: 'Initial Setup',
    path: 'cli/initial_setup_and_configuration.md',
    sectionId: 'cli',
    url: buildRawDocUrl('cli/initial_setup_and_configuration.md'),
    githubUrl: buildGithubDocUrl('cli/initial_setup_and_configuration.md'),
  },
  'cli-gpu-setup': {
    title: 'GPU Setup',
    path: 'cli/gpu_setup.md',
    sectionId: 'cli',
    url: buildRawDocUrl('cli/gpu_setup.md'),
    githubUrl: buildGithubDocUrl('cli/gpu_setup.md'),
  },
  'cli-importer-execution': {
    title: 'Importer And Testcase Execution',
    navTitle: 'Importer And Execution',
    path: 'cli/importer_and_testcase_execution.md',
    sectionId: 'cli',
    url: buildRawDocUrl('cli/importer_and_testcase_execution.md'),
    githubUrl: buildGithubDocUrl('cli/importer_and_testcase_execution.md'),
  },
  'cli-analysis-report': {
    title: 'Analysis And Report',
    path: 'cli/analysis_and_report.md',
    sectionId: 'cli',
    url: buildRawDocUrl('cli/analysis_and_report.md'),
    githubUrl: buildGithubDocUrl('cli/analysis_and_report.md'),
  },

  'tdms-dashboard-home': {
    title: 'UI',
    navTitle: 'Overview',
    path: 'ui/index.md',
    sectionId: 'ui',
    url: buildRawDocUrl('ui/index.md'),
    githubUrl: buildGithubDocUrl('ui/index.md'),
  },
  'tdms-dashboard-setup': {
    title: 'Local Setup (No Docker)',
    navTitle: 'Setup',
    path: 'ui/setup.md',
    sectionId: 'ui',
    url: buildRawDocUrl('ui/setup.md'),
    githubUrl: buildGithubDocUrl('ui/setup.md'),
  },
  'tdms-dashboard-architecture': {
    title: 'Architecture And Components',
    navTitle: 'Architecture',
    path: 'ui/architecture_and_components.md',
    sectionId: 'ui',
    url: buildRawDocUrl('ui/architecture_and_components.md'),
    githubUrl: buildGithubDocUrl('ui/architecture_and_components.md'),
  },
  'tdms-dashboard-auth': {
    title: 'Authentication And Roles',
    navTitle: 'Auth And Roles',
    path: 'ui/authentication_and_roles.md',
    sectionId: 'ui',
    url: buildRawDocUrl('ui/authentication_and_roles.md'),
    githubUrl: buildGithubDocUrl('ui/authentication_and_roles.md'),
  },
  'tdms-dashboard-manual-tdms': {
    title: 'TDMS Dashboard User Manual',
    navTitle: 'TDMS Dashboard',
    path: 'ui/tdms_dashboard_manual.md',
    sectionId: 'ui',
    url: buildRawDocUrl('ui/tdms_dashboard_manual.md'),
    githubUrl: buildGithubDocUrl('ui/tdms_dashboard_manual.md'),
  },
  'tdms-dashboard-manual-testruns': {
    title: 'Test Runs User Manual',
    navTitle: 'Test Runs',
    path: 'ui/test_runs_manual.md',
    sectionId: 'ui',
    url: buildRawDocUrl('ui/test_runs_manual.md'),
    githubUrl: buildGithubDocUrl('ui/test_runs_manual.md'),
  },
  'tdms-dashboard-manual-run-config': {
    title: 'Run Configuration User Manual',
    navTitle: 'Run Configuration',
    path: 'ui/run_configuration_manual.md',
    sectionId: 'ui',
    url: buildRawDocUrl('ui/run_configuration_manual.md'),
    githubUrl: buildGithubDocUrl('ui/run_configuration_manual.md'),
  },
  'tdms-dashboard-manual-analysis': {
    title: 'Analysis And Run Details User Manual',
    navTitle: 'Analysis And Details',
    path: 'ui/analysis_and_run_details_manual.md',
    sectionId: 'ui',
    url: buildRawDocUrl('ui/analysis_and_run_details_manual.md'),
    githubUrl: buildGithubDocUrl('ui/analysis_and_run_details_manual.md'),
  },
  'tdms-dashboard-api': {
    title: 'API Reference',
    navTitle: 'API Reference',
    path: 'ui/api_reference.md',
    sectionId: 'ui',
    url: buildRawDocUrl('ui/api_reference.md'),
    githubUrl: buildGithubDocUrl('ui/api_reference.md'),
  },
  'tdms-dashboard-troubleshooting': {
    title: 'Troubleshooting',
    navTitle: 'Troubleshooting',
    path: 'ui/troubleshooting.md',
    sectionId: 'ui',
    url: buildRawDocUrl('ui/troubleshooting.md'),
    githubUrl: buildGithubDocUrl('ui/troubleshooting.md'),
  },

  'pqet-home': {
    title: 'PQET',
    navTitle: 'Overview',
    path: 'pqet/index.md',
    sectionId: 'pqet',
    url: buildRawDocUrl('pqet/index.md'),
    githubUrl: buildGithubDocUrl('pqet/index.md'),
  },
  'pqet-setup': {
    title: 'PQET Setup',
    navTitle: 'Setup',
    path: 'pqet/setup.md',
    sectionId: 'pqet',
    url: buildRawDocUrl('pqet/setup.md'),
    githubUrl: buildGithubDocUrl('pqet/setup.md'),
  },
} as const;

export type DocId = keyof typeof docsConfig;

export const DOCS_CONFIG: Record<DocId, DocEntry> = docsConfig;
export const DOC_IDS = Object.keys(docsConfig) as DocId[];

export const DOC_SECTIONS: DocSection[] = [
  {
    id: 'overview',
    title: 'Overview',
    docIds: [
      'overview-home',
      'overview-ai-evaluation-tool',
      'overview-docker-run',
      'overview-tdms',
      'overview-pqet',
    ],
  },
  {
    id: 'cli',
    title: 'AI Evaluation Tool CLI',
    docIds: ['cli-home', 'cli-initial-setup', 'cli-gpu-setup', 'cli-importer-execution', 'cli-analysis-report'],
  },
  {
    id: 'docker-setup',
    title: 'Docker Setup',
    docIds: ['docker-setup-home', 'docker-setup-config', 'docker-setup-gpu', 'docker-setup-run-ui', 'docker-setup-run'],
  },
  {
    id: 'ui',
    title: 'UI',
    docIds: [
      'tdms-dashboard-home',
      'tdms-dashboard-setup',
      'tdms-dashboard-architecture',
      'tdms-dashboard-auth',
      'tdms-dashboard-manual-tdms',
      'tdms-dashboard-manual-testruns',
      'tdms-dashboard-manual-run-config',
      'tdms-dashboard-manual-analysis',
      'tdms-dashboard-api',
      'tdms-dashboard-troubleshooting',
    ],
  },
  {
    id: 'pqet',
    title: 'PQET',
    docIds: ['pqet-home', 'pqet-setup'],
  },
];

const DOC_ID_BY_PATH = new Map<string, DocId>(
  DOC_IDS.map((docId) => [normalizeDocPath(DOCS_CONFIG[docId].path), docId])
);

export function normalizeDocPath(path: string) {
  return path.replace(/^\.?\//, '').replace(/^docs\//, '').replace(/\\/g, '/');
}

export function getDocIdByPath(path: string) {
  return DOC_ID_BY_PATH.get(normalizeDocPath(path)) ?? null;
}

export function getRepositoryRawUrl(repoPath: string) {
  return buildRawRepositoryUrl(repoPath);
}

export function getRepositoryGithubUrl(repoPath: string) {
  return buildGithubRepositoryUrl(repoPath);
}
