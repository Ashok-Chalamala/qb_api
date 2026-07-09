# Cloud Run deployment guide for Quest Beyond API
# ─────────────────────────────────────────────────────────────────────────────
# Prerequisites:
#   - gcloud CLI installed and authenticated  (gcloud auth login)
#   - Docker Desktop running
#   - GCP project: questbeyond
#   - Artifact Registry repo created (or use Cloud Build / gcloud builds submit)
# ─────────────────────────────────────────────────────────────────────────────

# ── Variables ──────────────────────────────────────────────────────────────────
PROJECT_ID=questbeyond
REGION=us-central1
SERVICE=qb-api
REPO=questbeyond-docker           # Artifact Registry repo name
IMAGE=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$SERVICE

# ── 1. One-time: create Artifact Registry repository ─────────────────────────
gcloud artifacts repositories create $REPO \
  --project=$PROJECT_ID \
  --repository-format=docker \
  --location=$REGION \
  --description="Quest Beyond API images"

# ── 2. Authenticate Docker to Artifact Registry ───────────────────────────────
gcloud auth configure-docker $REGION-docker.pkg.dev

# ── 3. Build & push the image (run from repo root) ────────────────────────────
gcloud builds submit \
  --project=$PROJECT_ID \
  --tag $IMAGE:latest \
  --timeout=15m

# ─── OR build locally and push ────────────────────────────────────────────────
# docker build -t $IMAGE:latest .
# docker push $IMAGE:latest

# ── 4. Create a Secret Manager secret for the Vertex AI service account key ───
#       (never pass the JSON as a plain env var or bake it into the image)
gcloud secrets create vertex-sa-key \
  --project=$PROJECT_ID \
  --replication-policy=automatic

gcloud secrets versions add vertex-sa-key \
  --project=$PROJECT_ID \
  --data-file=/path/to/sa-key.json        # replace with your local path

# Grant Cloud Run's service account access to the secret
gcloud secrets add-iam-policy-binding vertex-sa-key \
  --project=$PROJECT_ID \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# ── 5. Deploy to Cloud Run ────────────────────────────────────────────────────
gcloud run deploy $SERVICE \
  --project=$PROJECT_ID \
  --image=$IMAGE:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --min-instances=0 \
  --max-instances=10 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=60 \
  --concurrency=80 \
  \
  # ── Environment variables ────────────────────────────────────────────────
  --set-env-vars="VERTEX_PROJECT=questbeyond" \
  --set-env-vars="VERTEX_LOCATION=us-central1" \
  --set-env-vars="VERTEX_MODEL=gemini-2.0-flash-001" \
  --set-env-vars="GOOGLE_REDIRECT_URI=https://<YOUR-CLOUD-RUN-URL>/google-health/callback" \
  \
  # ── Mount the SA key from Secret Manager ────────────────────────────────
  --set-secrets="/secrets/sa-key.json=vertex-sa-key:latest" \
  --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa-key.json"

# ── 6. Get the deployed URL ───────────────────────────────────────────────────
gcloud run services describe $SERVICE \
  --project=$PROJECT_ID \
  --region=$REGION \
  --format="value(status.url)"

# ── 7. Update Google OAuth redirect URI ──────────────────────────────────────
# After getting the Cloud Run URL (e.g. https://qb-api-xxxxx-uc.a.run.app):
#
# 1. Go to console.cloud.google.com → APIs & Services → Credentials
# 2. Edit your OAuth 2.0 Client ID
# 3. Add to Authorized redirect URIs:
#       https://qb-api-xxxxx-uc.a.run.app/google-health/callback
# 4. Save

# ── 8. Redeploy with final redirect URI (after step 7) ───────────────────────
gcloud run services update $SERVICE \
  --project=$PROJECT_ID \
  --region=$REGION \
  --update-env-vars="GOOGLE_REDIRECT_URI=https://qb-api-xxxxx-uc.a.run.app/google-health/callback"

# ── Rollback to previous revision ────────────────────────────────────────────
# gcloud run services update-traffic $SERVICE --to-revisions=PREVIOUS=100 --region=$REGION --project=$PROJECT_ID

# ── Local smoke test with Docker (before pushing) ────────────────────────────
# docker build -t qb-api-local .
# docker run --rm -p 8080:8080 \
#   -e VERTEX_PROJECT=questbeyond \
#   -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa-key.json \
#   -v /path/to/sa-key.json:/secrets/sa-key.json:ro \
#   qb-api-local
# curl http://localhost:8080/health
