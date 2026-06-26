# Foretell Frontend

Next.js + assistant-ui chat frontend for the existing Foretell FastAPI service.

## Run Locally

Start the backend first from the repository root:

```powershell
uv run uvicorn api.main:app --reload
```

Then start the frontend:

```powershell
cd frontend
pnpm dev
```

Open http://localhost:3000.

## Configuration

Copy `.env.local.example` to `.env.local` if you need to override defaults:

```powershell
Copy-Item .env.local.example .env.local
```

Defaults:

- `FORETELL_API_URL=http://127.0.0.1:8000`
- `FORETELL_USER_ID=test-user`

The frontend stores the returned Foretell `thread_id` in `localStorage` and sends it on later requests to keep the same conversation.
This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
