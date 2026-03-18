### Create project Structure

### Create folders
'''
mkdir src\agents\tools src\api src\shared infra frontend   .github\workflows
'''

### Create files
- User powershell instead of command due to limiation by design can only create one file at a time but not multiple in one command

- Powershell command
'''
$files = @(
  "src\agents\__init__.py"
  "src\agents\crew.py"
  "src\agents\agents.py"
  "src\agents\tasks.py"
  "src\agents\tools\__init__.py"
  "src\agents\tools\search.py"
  "src\agents\tools\scraper.py"
  "src\api\__init__.py"
  "src\api\main.py"
  "src\api\models.py"
  "src\api\routes.py"
  "src\shared\__init__.py"
  "src\shared\config.py"
  "src\shared\telemetry.py"
  "frontend\app.py"
  "frontend\requirements.txt"
  ".env.example"
  "Dockerfile"
)

New-Item $files -ItemType File -Force
'''


