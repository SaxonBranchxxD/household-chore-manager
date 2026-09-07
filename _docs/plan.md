# Household Chore Manager - Project Plan

## Project Overview

A mobile app for managing shared household chores across multiple groups/households. Users can assign chores, track completion, earn points, and view distribution stats.

## Core Features

### 1. **Chore Management**
   - Create one-time chores
   - Create weekly recurring chores
   - Assign chores to specific people
   - Add chores to a shared pool (anyone can claim)
   - Edit and delete chores
   - Mark chores as complete

### 2. **User Management**
   - User registration and authentication
   - Create/manage household groups
   - Add members to households
   - User roles (admin, member)

### 3. **Points & Rewards**
   - Award points for completed chores
   - Configurable points per chore
   - Leaderboards by household
   - Points history

### 4. **Analytics & Statistics**
   - Chore distribution stats (who's doing what)
   - Completion rates
   - Points earned over time
   - Member comparison

### 5. **Notifications**
   - Chore reminders
   - Assignment notifications
   - Recurring chore alerts

## Technology Stack

- **Backend:** Django + Django REST Framework (Python)
- **Frontend:** React Native (cross-platform mobile)
- **Database:** PostgreSQL
- **API:** RESTful JSON API
- **Authentication:** JWT tokens

## Data Models

### User
- id, email, password, first_name, last_name, created_at, updated_at

### Household
- id, name, owner, created_at, updated_at

### HouseholdMember
- id, household, user, role (admin/member), joined_at

### Chore
- id, household, title, description, assigned_to (nullable), points, frequency (one-time/weekly), due_date, created_by, created_at, updated_at

### ChoreCompletion
- id, chore, completed_by, completed_at, points_earned

### UserPoints
- id, user, household, total_points, last_updated

## API Endpoints (Preliminary)

```
POST   /api/auth/register
POST   /api/auth/login
GET    /api/households
POST   /api/households
GET    /api/households/:id/members
POST   /api/households/:id/members
GET    /api/households/:id/chores
POST   /api/households/:id/chores
PATCH  /api/chores/:id
DELETE /api/chores/:id
POST   /api/chores/:id/complete
GET    /api/households/:id/stats
GET    /api/households/:id/leaderboard
```

## Development Phases

### Phase 1: Backend Setup
- [ ] Django project setup
- [ ] Database models
- [ ] Authentication system
- [ ] Core API endpoints

### Phase 2: API Development
- [ ] Chore CRUD operations
- [ ] User and household management
- [ ] Points and statistics logic
- [ ] API testing

### Phase 3: Mobile App
- [ ] React Native setup
- [ ] Authentication UI
- [ ] Chore listing and creation
- [ ] Completion tracking UI

### Phase 4: Polish & Deploy
- [ ] Testing and bug fixes
- [ ] Performance optimization
- [ ] Deployment setup
- [ ] Documentation

## Success Criteria

- Users can create households and add members
- Chores can be created, assigned, and marked complete
- Points are correctly calculated and displayed
- Leaderboards show accurate rankings
- App is responsive on iOS and Android
- API is well-documented and tested
