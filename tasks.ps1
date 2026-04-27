<#
.SYNOPSIS
    PowerShell-friendly equivalent of the project Makefile. Mirrors every
    Makefile target so Windows users (or anyone who'd rather not install
    GNU Make) get the same experience.

.PARAMETER Task
    Name of the task to run. Run `.\tasks.ps1 help` for the full list.

.PARAMETER Profile
    Databricks CLI profile name. Defaults to $env:DBX_PROFILE, then to
    'DEFAULT'. Override per-invocation with `-Profile us-med-dev`.

.PARAMETER Target
    Bundle target name (matches `targets.<name>:` in databricks.yml).
    Default: 'dev'.

.PARAMETER AppName
    Databricks Apps app name. Default: 'velocia-newop-sdc'.

.EXAMPLE
    .\tasks.ps1 install
    .\tasks.ps1 build
    .\tasks.ps1 bundle-deploy -Profile us-med-dev
    .\tasks.ps1 seed-dev      -Profile us-med-dev
    .\tasks.ps1 app-restart   -Profile us-med-dev
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory, Position=0)]
    [ValidateSet(
        'help','install','install-backend','install-frontend',
        'dev-backend','dev-frontend','build','db-reset',
        'test','test-backend','test-frontend','lint','fake-agent','clean',
        'bundle-validate','bundle-deploy','bundle-destroy',
        'seed-dev','app-status','app-logs','app-restart'
    )]
    [string]$Task,

    [string]$Profile = $(if ($env:DBX_PROFILE) { $env:DBX_PROFILE } else { 'DEFAULT' }),
    [string]$Target  = 'dev',
    [string]$AppName = 'velocia-newop-sdc'
)

$ErrorActionPreference = 'Stop'

function Assert-LastExit {
    param([string]$What)
    if ($LASTEXITCODE -ne 0) {
        throw "$What failed (exit code $LASTEXITCODE)"
    }
}

function Get-WorkspaceEmail {
    $json = databricks --profile $Profile current-user me -o json
    Assert-LastExit "databricks current-user me"
    return ($json | ConvertFrom-Json).emails[0].value
}

function Show-Help {
    @"
Usage: .\tasks.ps1 <task> [-Profile <name>] [-Target <env>] [-AppName <name>]

Local dev:
  install            install backend + frontend deps
  install-backend    pip install -e ".[dev]"
  install-frontend   npm install (in frontend/)
  dev-backend        uvicorn backend.main:app --reload --port 8000
  dev-frontend       npm run dev (vite on :5173)
  build              build the SPA bundle into frontend/dist
  db-reset           delete local.db (init_db() recreates the schema next boot)
  test               pytest (backend)
  lint               ruff + tsc --noEmit
  fake-agent         run a local stub of the Agent API on :9000
  clean              wipe build artifacts and caches

Databricks Asset Bundle (target=$Target profile=$Profile):
  bundle-validate    databricks bundle validate
  bundle-deploy      build + bundle deploy + apps start + apps deploy --source-code-path
  bundle-destroy     databricks bundle destroy --auto-approve
  seed-dev           python scripts\seed_dev.py
  app-status         databricks apps get
  app-logs           tail recent app logs (or print logz URL)
  app-restart        stop + start
"@ | Write-Host
}

# ---- Local dev tasks --------------------------------------------------------

function Invoke-InstallBackend  { pip install -e ".[dev]"; Assert-LastExit "pip install" }
function Invoke-InstallFrontend { Push-Location frontend; try { npm install; Assert-LastExit "npm install" } finally { Pop-Location } }
function Invoke-Install         { Invoke-InstallBackend; Invoke-InstallFrontend }

function Invoke-DevBackend      { uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 }
function Invoke-DevFrontend     { Push-Location frontend; try { npm run dev } finally { Pop-Location } }

function Invoke-Build           { Push-Location frontend; try { npm run build; Assert-LastExit "npm run build" } finally { Pop-Location } }

function Invoke-DbReset {
    if (Test-Path local.db) { Remove-Item local.db -Force }
    Write-Host "local.db removed; next backend start will recreate the schema via init_db()."
}

function Invoke-TestBackend     { pytest; Assert-LastExit "pytest" }
function Invoke-TestFrontend    { Push-Location frontend; try { npm test --if-present } finally { Pop-Location } }
function Invoke-Test            { Invoke-TestBackend }

function Invoke-Lint {
    ruff check backend tests; Assert-LastExit "ruff check"
    Push-Location frontend; try { npx tsc --noEmit; Assert-LastExit "tsc --noEmit" } finally { Pop-Location }
}

function Invoke-FakeAgent { uvicorn tests.backend.fake_agent:app --host 0.0.0.0 --port 9000 }

function Invoke-Clean {
    foreach ($p in 'frontend\dist','.pytest_cache','.ruff_cache','.mypy_cache') {
        if (Test-Path $p) { Remove-Item -Recurse -Force $p }
    }
    Get-ChildItem -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force
}

# ---- Bundle / deploy tasks --------------------------------------------------

function Invoke-BundleValidate {
    databricks bundle validate -t $Target --profile $Profile
    Assert-LastExit "bundle validate"
}

function Invoke-BundleDeploy {
    Invoke-Build

    databricks bundle deploy -t $Target --profile $Profile
    Assert-LastExit "bundle deploy"

    Write-Host ">>> Ensuring app compute is started..."
    # `apps start` returns non-zero if the app is already RUNNING; tolerate it.
    databricks --profile $Profile apps start $AppName 2>$null
    $LASTEXITCODE = 0

    Write-Host ">>> Pushing app source code from the bundle workspace path..."
    $email = Get-WorkspaceEmail
    $sourcePath = "/Workspace/Users/$email/.bundle/velocia-newop-sdc/$Target/files"
    Write-Host "    source-code-path: $sourcePath"
    databricks --profile $Profile apps deploy $AppName --source-code-path $sourcePath
    Assert-LastExit "apps deploy"
}

function Invoke-BundleDestroy {
    databricks bundle destroy -t $Target --profile $Profile --auto-approve
    Assert-LastExit "bundle destroy"
}

function Invoke-SeedDev {
    python scripts\seed_dev.py --profile $Profile --app $AppName
    Assert-LastExit "seed_dev.py"
}

function Invoke-AppStatus {
    databricks --profile $Profile apps get $AppName
    Assert-LastExit "apps get"
}

function Invoke-AppLogs {
    # `apps logs` requires OAuth — PAT-based profiles fail with
    # 'OAuth Token not supported'. Try a sibling -oauth profile first; fall
    # back to printing the /logz URL the user can open in a browser.
    $oauthProfile = "$Profile-oauth"
    databricks --profile $oauthProfile apps logs $AppName --tail-lines 200 2>$null
    if ($LASTEXITCODE -ne 0) {
        $LASTEXITCODE = 0
        $info = databricks --profile $Profile apps get $AppName --output json
        $url  = ($info | ConvertFrom-Json).url
        Write-Host "Run-time logs: $url/logz"
    }
}

function Invoke-AppRestart {
    databricks --profile $Profile apps stop $AppName 2>$null
    $LASTEXITCODE = 0
    databricks --profile $Profile apps start $AppName
    Assert-LastExit "apps start"
}

# ---- Dispatch ---------------------------------------------------------------

switch ($Task) {
    'help'             { Show-Help }
    'install'          { Invoke-Install }
    'install-backend'  { Invoke-InstallBackend }
    'install-frontend' { Invoke-InstallFrontend }
    'dev-backend'      { Invoke-DevBackend }
    'dev-frontend'     { Invoke-DevFrontend }
    'build'            { Invoke-Build }
    'db-reset'         { Invoke-DbReset }
    'test'             { Invoke-Test }
    'test-backend'     { Invoke-TestBackend }
    'test-frontend'    { Invoke-TestFrontend }
    'lint'             { Invoke-Lint }
    'fake-agent'       { Invoke-FakeAgent }
    'clean'            { Invoke-Clean }
    'bundle-validate'  { Invoke-BundleValidate }
    'bundle-deploy'    { Invoke-BundleDeploy }
    'bundle-destroy'   { Invoke-BundleDestroy }
    'seed-dev'         { Invoke-SeedDev }
    'app-status'       { Invoke-AppStatus }
    'app-logs'         { Invoke-AppLogs }
    'app-restart'      { Invoke-AppRestart }
}
