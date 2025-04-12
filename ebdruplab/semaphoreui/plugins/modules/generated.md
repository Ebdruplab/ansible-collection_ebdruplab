Awesome — thanks for listing your current module coverage! Based on your existing modules:

---

### ✅ **You already have these 33 modules:**

| **Type**        | **Files** |
|------------------|-------------------------------------------------------------------|
| **Core**         | `login`, `logout`, `ping`, `info`, `websocket_status`             |
| **User**         | `user_get`, `user_list`, `user_delete`, `user_password_update`    |
| **User Tokens**  | `user_token_get`, `user_token_create`, `user_token_delete`        |
| **Project**      | `project_list`, `project_get`, `project_create`, `project_update`, `project_delete`, `project_restore`, `project_backup`, `project_events`, `project_role` |
| **Schedule**     | `schedule_create`, `schedule_get`, `schedule_update`, `schedule_delete` |
| **Events**       | `events`, `events_last`                                            |
| **Template**     | `template_list`, `template_get`, `template_create`, `template_update`, `template_delete` |

---

### ❗ **Missing API Modules (based on 85 endpoints)**

Here’s what you **don’t have** yet, grouped by category:

---

#### 🔐 **Authentication (OIDC)**
- [ ] `auth_login_get` – Fetch login metadata
- [ ] `auth_login_post` – Perform login
- [ ] `auth_logout_post` – Destroy session
- [ ] `auth_oidc_login_get`
- [ ] `auth_oidc_redirect_get`

---

#### 👤 **Users**
- [x] `user_get` ✅
- [x] `user_list` ✅
- [x] `user_delete` ✅
- [x] `user_password_update` ✅
- [ ] `user_create` – `POST /users`
- [ ] `user_update` – `PUT /users/{user_id}`

---

#### 🗃️ **Projects**
- [x] Core CRUD ✅
- [ ] `project_users_list` – `GET /project/{id}/users`
- [ ] `project_users_add` – `POST /project/{id}/users`
- [ ] `project_users_update` – `PUT /project/{id}/users/{user_id}`
- [ ] `project_users_remove` – `DELETE /project/{id}/users/{user_id}`

---

#### 🔑 **Keys**
- [ ] `project_keys_list`
- [ ] `project_keys_create`
- [ ] `project_keys_update`
- [ ] `project_keys_delete`

---

#### 🌍 **Environment**
- [ ] `environment_list`
- [ ] `environment_create`
- [ ] `environment_get`
- [ ] `environment_update`
- [ ] `environment_delete`

---

#### 🧾 **Inventory**
- [ ] `inventory_list`
- [ ] `inventory_create`
- [ ] `inventory_get`
- [ ] `inventory_update`
- [ ] `inventory_delete`

---

#### 🔌 **Integrations**
- [ ] `integration_list`
- [ ] `integration_create`
- [ ] `integration_update`
- [ ] `integration_delete`
- [ ] `integration_values_add`
- [ ] `integration_values_get`
- [ ] `integration_values_update`
- [ ] `integration_values_delete`
- [ ] `integration_matchers_add`
- [ ] `integration_matchers_get`
- [ ] `integration_matchers_update`
- [ ] `integration_matchers_delete`

---

#### 📁 **Repositories**
- [ ] `repository_list`
- [ ] `repository_create`
- [ ] `repository_get`
- [ ] `repository_update`
- [ ] `repository_delete`

---

#### 👀 **Views**
- [ ] `view_list`
- [ ] `view_create`
- [ ] `view_get`
- [ ] `view_update`
- [ ] `view_delete`

---

#### 📦 **Tasks**
- [ ] `tasks_list`
- [ ] `tasks_last`
- [ ] `task_get`
- [ ] `task_create`
- [ ] `task_stop`
- [ ] `task_delete`
- [ ] `task_output`
- [ ] `task_raw_output`

---

### ✅ Recap

| **Status**     | **Count** |
|----------------|-----------|
| Already Built  | 33        |
| Remaining      | **52**    |
| **Total API**  | **85**    |
