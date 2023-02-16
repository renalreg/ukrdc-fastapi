# `test_routers`

## Test scope

In an effort to keep these tests even remotely maintainable with the small team we have, the router tests are limited to the following:

* Permission checks
  * Does the route return a 403 if the user is missing a permission?
  * Does the route return a 200 if the user has the permission?
  * Are lists of resources filtered by the user's permissions?
* Bare minimum validation where required
* Logic contained only within the router function
