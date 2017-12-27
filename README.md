# SimpleSync

A basic Sublime Text 3 plugin that listens to `save` event and [r]sync the file to remote automatically.

## Installation

Clone this repo into `Packages` folder:

```bash
cd [...]/Sublime Text 3/Data/Packages
git clone https://github.com/ushuz/SimpleSync.git
```

## Settings

Preferences > Package Settings > SimpleSync > Settings - User

Sample settings:

```
{
  "projects": [
    {
      "local": "/Users/John/projects",
      "remote": "/home/john/projects",

      // If you want to execute commands outside default PATH, provide their
      // paths here.
      "path": "~/myhandycommands:/usr/local/bin",

      // You can specify multiple commands to execute, that's pretty neat if
      // you have multiple destinations. Currently, only rsync is supported.
      "commands": [
        "rsync -avz {local} remote1:{remote}",
        "rsync -avz {local} remote2:{remote}",
      ],

      // Skip files that match the patterns.
      "excludes": [],

      // Specify command execution timeout, defaults to 10.
      "timeout": 10,
    }
  ]
}
```
