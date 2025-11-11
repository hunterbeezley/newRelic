#### First, run `filterIds` to filter user IDs by X days ago and ensure proper formatting for massDeleteUsers.
If you already have a dict of ready-to-delete user IDs that match the below format, then you can skip ahead to massdeleteUsers.
```
{
  "userIds": [
    "user-id-1",
    "user-id-2",
    "user-id-3"
  ]
}
```
