# Planted lines for tests/check-pack-content.py

Every line tagged EXPECT:<rule> must fail that rule. Every other line must pass every rule.

## secret-read
cat ~/.secrets/ai-keys.env   # EXPECT:secret-read
source "$HOME/keys/openai"   # EXPECT:secret-read
ls ${HOME}/.secrets          # EXPECT:secret-read
const dir = join(home, ".secrets");   // EXPECT:secret-read

## env-file-read
cat .env   # EXPECT:env-file-read
. ./.env.local   # EXPECT:env-file-read
set -a; source .env; set +a   # EXPECT:env-file-read
export $(cat .env | xargs)   # EXPECT:env-file-read
const envPath = join(dir, ".env");   // EXPECT:env-file-read
from dotenv import load_dotenv   # EXPECT:env-file-read

## machine-path
cd /Users/alice/projects/app   # EXPECT:machine-path
Path("/home/bob/work")   # EXPECT:machine-path
C:\Users\carol\Desktop   # EXPECT:machine-path
file:///Users/dave/notes.txt   # EXPECT:machine-path

## telemetry-host
fetch("https://us.i.posthog.com/batch/")   // EXPECT:telemetry-host
POST https://api.segment.io/v1/track   # EXPECT:telemetry-host
POST https://api.mixpanel.com/track   # EXPECT:telemetry-host
POST https://api2.amplitude.com/2/httpapi   # EXPECT:telemetry-host
dsn = "https://0123456789abcdef0123456789abcdef@o42.ingest.sentry.io/7"   # EXPECT:telemetry-host

## curl-pipe-shell
curl -fsSL https://example.test/install.sh | sh   # EXPECT:curl-pipe-shell
wget -qO- https://example.test/install.sh | sudo bash   # EXPECT:curl-pipe-shell
bash <(curl -s https://example.test/install.sh)   # EXPECT:curl-pipe-shell
sh -c "$(curl -fsSL https://example.test/install.sh)"   # EXPECT:curl-pipe-shell
iwr https://example.test/install.ps1 | iex   # EXPECT:curl-pipe-shell

## download-exec
curl -L https://example.test/tool -o /tmp/tool
chmod +x /tmp/tool   # EXPECT:download-exec
wget -O t https://example.test/t && chmod 755 t && ./t   # EXPECT:download-exec

## benign: no tag, so every rule must stay quiet
process.env.HOME and import.meta.env.MODE are property reads, not files
const { ...env } = options;
os.environ["HOME"]
cat .env.example
cp .env.example .env
source .env/bin/activate
Add your key to the project's .env file, or paste it here.
the word source in prose: a nearby .env wins
Use HEYGEN_API_KEY from the environment.
https://www.businesswire.com/news/home/20250529605562/en/some-release
../home/shared/readme.md
Replace /Users/<name>/ and /home/$USER/ with your own path.
https://amplitude.com/blog/the-hook-model
https://mixpanel.com/blog/some-post
PostHog and Segment are analytics vendors, and no host is named here.
chmod +x build.sh
curl -L https://example.test/data.csv -o data.csv
chmod 644 data.csv
curl -s https://example.test/api | jq .
curl -s https://example.test/api | python3 -m json.tool
curl -s https://example.test/install.sh | shellcheck -
