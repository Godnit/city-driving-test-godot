# Halaqa Phase 4 — Mosque accounts, synchronization, and sticky sheet tabs

This phase starts from the 3.1.6 application build.

## Implemented first

1. Keep the حفظ / مراجعة switch visible while scrolling.
2. Preserve an independent scroll position for each sheet.
3. Add the cloud-account UI shell and synchronization status states.
4. Define the Firestore data model and security rules for one mosque with admin and teacher accounts.

## Cloud model

- `users/{uid}`: the signed-in user's mosque, role, group, and active state.
- `mosques/{mosqueId}`: mosque information and owner.
- `mosques/{mosqueId}/members/{uid}`: admin or teacher membership.
- `mosques/{mosqueId}/groups/{groupId}`: halaqa/group details.
- `mosques/{mosqueId}/students/{studentId}`: students.
- `mosques/{mosqueId}/recitations/{recordId}`: memorization and review records.
- `mosques/{mosqueId}/attendance/{recordId}`: attendance and deductions.
- `mosques/{mosqueId}/notes/{recordId}`: notes.
- `mosques/{mosqueId}/holidays/{recordId}`: weekly and sudden holidays.
- `mosques/{mosqueId}/settings/main`: mosque-wide settings.

Every synchronized record carries `mosqueId`, `updatedAt`, and `updatedBy`. Teacher-owned records also carry `teacherId` and `groupId`.

## Roles

- `admin`: reads all mosque data, manages teachers and groups, and exports all reports.
- `teacher`: reads the mosque roster assigned to them and writes only records for their assigned group.

## Required before live synchronization can be enabled

A Firebase project must be created and its Web App configuration placed in `firebase-config.js`. Email/password sign-in and Cloud Firestore must be enabled, and the included security rules must be deployed.
