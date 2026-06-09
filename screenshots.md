# Screenshots & UI Mockups

> Live screenshots are generated automatically after running `docker compose up`. The mockup PNGs below ship in `docs/img/` and illustrate the intended look-and-feel.

| View | Description | File |
|------|-------------|------|
| Login | Centered card on a brand-gradient background | `docs/img/login.png` |
| Dashboard | KPI tiles + recent datasets + recent reports | `docs/img/dashboard.png` |
| Datasets | Table view of uploaded files with Generate / Delete actions | `docs/img/datasets.png` |
| Report Detail | Executive summary, KPI grid, charts, insights, recommendations, chatbot | `docs/img/report-detail.png` |
| Architecture | High-level system diagram | `docs/img/architecture.png` |

To capture your own screenshots after deployment, use the browser's full-page-screenshot devtool or `playwright`:
```bash
npx playwright screenshot http://localhost docs/img/dashboard.png --full-page
```
