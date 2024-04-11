# Pi-Cam

This is a Raspberry Pi Security Camera.

## First time setup

This project uses Apache. Make sure it is installed (`sudo apt install apache2`).

When Apache is running it uses a user named `www-data` to serve files and run CGI scripts. `www-data` will need to run CGI scripts that access `/dev/media#`, requiring `www-data` to be in the `video` group.

```bash
sudo useradd www-data video
```

The `apache-setup.sh` script will do the rest:
* Move files
* Create directories
* Change file permissions
* Start apache2.service

Be sure to run it with sudo.
