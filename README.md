# OpenWRT Image generator

This collection of python scripts enable one to compile custom OpenWRT
images at mass. One configures a set of devices with their special
requirements and a set of templates with their special requirements using
YAML. These scripts then build the cartesian product of templates and
devices in order to get you your desired images.

## Ussage
I assume that you already [installed all required packages](https://openwrt.org/docs/guide-developer/toolchain/install-buildsystem) for building
OpenWRT on the host. The following steps are required in order to build images:

1. Create a folder on your hard disk and cd into it (the script will cludder
   the working directory a bit). The filesystem should have a couple GB
   of avaiable storage.

2. Clone this repo. (`git clone "https://github.com/Doralitze/owrt-image-generator.git" bin`)
3. Place your build config inside this directory. An example config is shown below.
4. Run the script (`python3 bin/owrt-image-generator/main.py -vvvvv`).
5. After the script ran the generated images are locaed within the `out` directory within
   their appropriate sub folder.
6. Clean the build directory prior to the next build.

## Example config file
```yaml
---
- branch: "v19.07.7" # Change to your preferred branch or tag
  # you may also specify a repo: setting in order to use a different repository.
  
  # In this example config file we're using openwrt to build controller based access points.
  # Of course you can do whatever you like.
  extra_feeds:
      - "src-git openwisp https://github.com/openwisp/openwisp-config.git"
  # We need to define templates for every desired device role
  templates:
      - name: "my_accesspoint_template"
        files:
            - path: "etc/config/openwisp"
              content: "config controller 'http'\n
                        \toption url '<<YOUR CONTROLLER URL>>'\n
                        \toption shared_secret '<<YOUR SECRET CONTROLLER KEY>>'\n"
            - path: "/etc/crontabs/root"
              content: '@reboot sh -c "/usr/bin/killall ntpclient && /usr/sbin/ntpclient -c 1 -s -h pool.ntp.org &"'
            - path: "/etc/dropbear/authorized_keys"
              content: "ssh-rsa <<YOUR FIRST KEY\n
                        ssh-rsa <<YOUR SECOND KEY>\n"
        settings:
            - "CONFIG_PACKAGE_openwisp-config-openssl=y"
            - "CONFIG_LIBCURL_OPENSSL=y"
            - "CONFIG_ZABBIX_NOSSL=n"
            - "CONFIG_PACKAGE_htop=y"
            - "CONFIG_DEFAULT_ppp=n"
            - "CONFIG_DEFAULT_ppp-mod-pppoe=n"
            - "CONFIG_DEFAULT_wpad-basic=n"
            - "CONFIG_PACKAGE_wpad=y"
            - "CONFIG_PACKAGE_wpad-mesh-openssl=m"
            - "CONFIG_PACKAGE_dmesg=y"
            - "CONFIG_PACKAGE_iwinfo=y"
            - "CONFIG_PACKAGE_kmod=y"
            - "CONFIG_PACKAGE_ca-bundle=y"
  # And then we need to define the specifics of our devices
  devices:
      - name: "ubnt_ap_ac_pro"
        settings:
            - "CONFIG_TARGET_ath79_generic_DEVICE_ubnt_unifiac-pro=y"
```
