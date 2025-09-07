# V1.0.0
Initial release.

# V1.1.0


patch: fixes issue where in Dwcom would not recognize that speechInterrupt was set to false.
patch: Makes speach output say left/joined channel root rather than left/joined channel the root channel.
feat: Allows the use of logins and logouts txt files to create random login and logout messages.

# V1.1.1

patch: Fixes error in fileRandomizer that was caused by the improper use of file read/write flags.

# V1.2.0

feat: Sound playback now uses cyal and soundfile, which should resolve any prier issues with playing sounds and allow for more file formats.
feat: Dwcom now watches for config changes, the user is no longer required to refresh the config every time something changes.
patch: improoves cacheing to avoide issues with left over user ids. This should also remove the issue of errors about user type collection.
