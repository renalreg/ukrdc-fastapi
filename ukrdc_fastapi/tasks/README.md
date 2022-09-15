# tasks

Code related to our internal trackable background tasks.

We use trackable background tasks for a few reasons. First, it allows API users to perform longer running operations such as large data exports without having to wait for the operation to complete. Second, it allows us to track the progress of the operation, and provide feedback to the user. E.g. we can poll the task and report the current progress of the operation.

Tasks can be marked as private, so only the user who created the task can access it. This is useful for operations such as data exports, where we don't want to expose the data to other users. Alternatively, tasks can be marked as public, so that any user can access it.

We also use background tasks to track and manage some scheduled long-running operations such as scheduled cache refreshes. These tasks appear to have been started by an internal administrator user.
