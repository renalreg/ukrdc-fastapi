# query

This really is the key part of this application. The modules here handle retreiving, filtering, and sorting database queries before being passed to the API router for marshalling.

Critically, each module here also includes methods for handling permission-based access.

The API router is able to either grant or deny access to an API route based on permissions, however it cannot restrict access to resources based on properties of those resources. For example, a patient record should only be accessible by users with permission to view records from their unit/facility.

Additionally, routes mapping to lists of resources, for example a list of patient records, need to be filtered based on permission. We cannot simply allow or deny access.

Each module here should include an `_apply_query_permissions` function, which takes a query for a list of resources and filters based on user permissions. Also, an `_assert_permission` function handles a users access to a specific resource, raising a suitable HTTP exception if the user does not have permission to access this resource.

Note, that the permission-based filtering here augments API-level access control. For example, a user may have access to a patientrecord because of unit/facility permissions, but the user cannot modify that resource if they don't have write permission. That denial of access is handled by the API route security.
