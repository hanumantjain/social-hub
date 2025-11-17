# GalleryAI

GalleryAI is a full-stack social media gallery that allows users to create an account, upload posts with images and metadata, browse the global feed, and manage their profile. The system is built with a FastAPI backend (deployed on AWS Lambda via SAM/API Gateway) and a React frontend (deployed to S3/CloudFront with Vite and Tailwind). PostgreSQL powers persistence, and Google OAuth is integrated for passwordless authentication.

## Features

- **User Accounts**  
  Traditional username/password signup and login with JWT sessions, plus one-click Google OAuth.

- **Post Management**  
  Upload images via presigned S3 URLs, attach titles/captions/tags, view counts, and download tracking.

- **Feed & Profiles**  
  Infinite feed rendering, per-user galleries, editable profile info, and responsive design for mobile.

- **Production-Ready Deployment**  
  AWS SAM Lambda backend with migrations on startup, CORS hardening, Jenkins CI/CD, and environment-driven configuration.

## Tech Stack

| Layer        | Technology |
|--------------|------------|
| Frontend     | React 19, Vite, Tailwind, React Router, @react-oauth/google |
| Backend      | FastAPI, SQLAlchemy, JWT (python-jose), Mangum |
| Database     | PostgreSQL + SQL migrations |
| Auth         | Password (Argon2 hashing) + Google OAuth |
| Storage      | AWS S3 (presigned uploads) |
| Deployment   | AWS Lambda/API Gateway (backend), S3/CloudFront (frontend), Jenkins CI/CD |
| Infrastructure| AWS SAM template, SSM Parameter Store, IAM roles |

## Development Setup

```bash
git clone https://github.com/hanumantjain/galleryai.git
cd galleryai

# Backend
cd server
pip install -r requirements.txt
cp .env.example .env   # configure DATABASE_URL, SECRET_KEY, etc.
uvicorn main:app --reload

# Frontend
cd ../client
npm install
npm run dev
```

Docker compose is available (`docker-compose.yml`) for local full-stack testing with PostgreSQL.

## Environment Variables

Key variables (stored in SSM for production):

- `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `S3_BUCKET_NAME`, `GOOGLE_CLIENT_ID`, `CORS_ORIGINS`
- Frontend build requires `VITE_API_URL` and `VITE_GOOGLE_CLIENT_ID`

## Deployment Pipeline

1. **Build Client** – Jenkins retrieves Google Client ID/API URL from SSM, runs `npm run build`, and syncs `client/dist` to S3 with proper cache headers.  
2. **Build Server** – Runs `sam build` in `/server`.  
3. **Deploy Server** – `sam deploy` provisions API Gateway, Lambda, IAM, and environment configuration.  
4. **CloudFront Invalidation** – Ensures new frontend assets are served immediately.

## Google OAuth Flow

The frontend uses `@react-oauth/google` to obtain Google user info, then posts the verified profile (ID/email/name) to `/auth/google`. The backend creates or links accounts and returns a JWT, avoiding Lambda network calls to Google.

## Folder Structure

```
client/   # React app (Vite, Tailwind)
server/   # FastAPI backend, migrations, SAM template
docker-compose.yml  # optional local stack
Jenkinsfile         # CI/CD pipeline definition
```

## License

© 2025 Hanumant Jain. All rights reserved. Contact for licensing or contributions.
