# Household Chore Manager

A mobile app for managing shared household chores across multiple groups.

## Overview

This project allows multiple households/groups to:
- Assign chores to specific people or add to a shared pool
- Create one-time and weekly recurring chores
- Track completion history
- Earn points for completed chores
- View chore distribution stats and leaderboards

## Tech Stack

- **Backend:** Django with Django REST Framework
- **Frontend:** React Native (mobile)
- **Database:** PostgreSQL
- **Deployment:** TBD

## Getting Started

See `_docs/plan.md` for the full project plan.

```bash
# Clone the repository
git clone https://github.com/SaxonBranchxxD/household-chore-manager.git
cd household-chore-manager

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

## Project Structure

```
household-chore-manager/
├── _docs/
│   └── plan.md
├── chore_manager/          # Django project
├── chores/                 # Django app
├── requirements.txt
├── .gitignore
└── README.md
```

## License

TBD
