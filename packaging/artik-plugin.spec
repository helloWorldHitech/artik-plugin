%define __jar_repack 0

Name:		artik-plugin
Summary:	ARTIK plugin files for fedora
Version:	0.2
Release:	1
Group:		System Environment/Base
License:	none

Requires:       systemd
Requires:       setup
Requires:       pulseaudio
Requires:       bluez
Requires:       connman
Requires:       dnsmasq
Requires:       java-1.8.0-openjdk

Source0:	%{name}-%{version}.tar.gz

%description
ARTIK plugin files for fedora

%prep
%setup -q

%install
rm -rf %{buildroot}

# determine arch and OS for rpm
mkdir -p %{buildroot}/etc/rpm
cp -f scripts/platform %{buildroot}/etc/rpm

mkdir -p  %{buildroot}/etc/bluetooth
cp -r prebuilt/bluetooth/common/* %{buildroot}/etc/bluetooth

mkdir -p %{buildroot}/usr/lib/systemd/system
cp scripts/units/rfkill-unblock.service %{buildroot}/usr/lib/systemd/system

mkdir -p %{buildroot}/etc/udev/rules.d
cp scripts/rules/10-local.rules %{buildroot}/etc/udev/rules.d

mkdir -p %{buildroot}/etc/profile.d
cp scripts/open-jdk.sh %{buildroot}/etc/profile.d

# network
mkdir -p %{buildroot}/etc/sysconfig/network-scripts
cp prebuilt/network/ifcfg-eth0 %{buildroot}/etc/sysconfig/network-scripts

mkdir -p %{buildroot}/usr/bin
cp prebuilt/network/zigbee_version %{buildroot}/usr/bin

cp -r prebuilt/connman/* %{buildroot}

# audio
mkdir -p %{buildroot}/usr/lib/systemd/system
cp scripts/units/pulseaudio.service %{buildroot}/usr/lib/systemd/system
cp scripts/units/audiosetting.service %{buildroot}/usr/lib/systemd/system

# adbd
mkdir -p %{buildroot}/usr/bin
cp prebuilt/adbd/adbd %{buildroot}/usr/bin

mkdir -p %{buildroot}/usr/lib/systemd/system
cp scripts/units/adbd.service %{buildroot}/usr/lib/systemd/system
cp scripts/units/rndis.service %{buildroot}/usr/lib/systemd/system
cp scripts/rules/99-adb-restart.rules %{buildroot}/etc/udev/rules.d

# CoAP californium
mkdir -p %{buildroot}/opt/californium
cp -r prebuilt/californium/* %{buildroot}/opt/californium/

# lwM2M leshan
mkdir -p %{buildroot}/opt/leshan
cp -r prebuilt/leshan/* %{buildroot}/opt/leshan/

# systemd module load service
mkdir -p %{buildroot}/etc/systemd/system
cp scripts/units/systemd-modules-load.service %{buildroot}/etc/systemd/system

# booting done service
mkdir -p %{buildroot}/usr/bin
cp scripts/booting-done.sh %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/lib/systemd/system
cp scripts/units/booting-done.service %{buildroot}/usr/lib/systemd/system

%post
# Setting default runlevel to multi-user text mode
rm -f /etc/systemd/system/default.target
ln -s /lib/systemd/system/multi-user.target /etc/systemd/system/default.target

# Limit journal size
sed -i "s/#SystemMaxUse=/SystemMaxUse=10M/" /etc/systemd/journald.conf

# wpa_supplicant
sed -i 's/INTERFACES=\"\"/INTERFACES=\"-iwlan0\"/g' /etc/sysconfig/wpa_supplicant
sed -i 's/DRIVERS=\"\"/DRIVERS=\"-Dnl80211\"/g' /etc/sysconfig/wpa_supplicant

# Enable units
systemctl enable systemd-timesyncd.service
systemctl enable systemd-resolved.service
systemctl enable booting-done.service
systemctl enable rfkill-unblock.service

# systemd module load service
systemctl enable systemd-modules-load.service

# Dnsmasq setting
sed -i 's/\#except-interface=/except-interface=lo/g'  /etc/dnsmasq.conf

# Install java alternatives
/usr/sbin/alternatives --install /usr/bin/java java /usr/java/default/jre/bin/java 1
/usr/sbin/alternatives --install /usr/bin/javaws javaws /usr/java/default/jre/bin/javaws 1
/usr/sbin/alternatives --install /usr/bin/javac javac /usr/java/default/bin/javac 1
/usr/sbin/alternatives --install /usr/bin/jar jar /usr/java/default/bin/jar 1

# Sync after sshd key generation
echo "ExecStartPost=/usr/bin/sync" >> /usr/lib/systemd/system/sshd-keygen.service
sed -i 's/ConditionPathExists/ConditionFileNotEmpty/g' /usr/lib/systemd/system/sshd-keygen.service

###############################################################################
# artik-plugin

%files
%attr(0644,root,root) /etc/rpm/platform
%attr(0644,root,root) /etc/systemd/system/systemd-modules-load.service
%attr(0755,root,root) /usr/bin/booting-done.sh
%attr(0644,root,root) /usr/lib/systemd/system/booting-done.service
%attr(0644,root,root) /etc/profile.d/open-jdk.sh
%attr(0644,root,root) /usr/lib/systemd/system/rfkill-unblock.service

%attr(0755,root,root) /opt/californium/*.jar
%attr(0644,root,root) /opt/californium/lib/*.jar
%attr(0755,root,root) /opt/leshan/*.jar
%attr(0644,root,root) /opt/leshan/lib/*.jar

###############################################################################
# Bluetooth
# ARTIK common
%package bluetooth-common
Summary:    bluetooth
Group:		System
Requires:	bluez

%description bluetooth-common
Bluetooth

%post bluetooth-common
systemctl enable bluetooth.service

%files bluetooth-common
%attr(0644,root,root) /etc/udev/rules.d/10-local.rules
/etc/bluetooth/*

###############################################################################
# network
# ARTIK common
%package network-common
Summary:    network
Group:		System

%description network-common
Network Driver and DHCP configuration

%post network-common
systemctl enable connman.service

%files network-common
%attr(0644,root,root) /etc/sysconfig/network-scripts/ifcfg-eth0
%attr(0755,root,root) /usr/bin/zigbee_version
%attr(0644,root,root) /etc/connman/main.conf
%attr(0644,root,root) /var/lib/connman/settings

###############################################################################
# audio
# ARTIK common
%package audio-common
Summary:    audio
Group:		System
Requires:       pulseaudio

%description audio-common
audio

%post audio-common
systemctl enable pulseaudio.service
systemctl enable audiosetting.service

sed -i 's/load-module module-udev-detect/load-module module-udev-detect tsched=0/g' /etc/pulse/default.pa
echo "load-module module-switch-on-connect" >> /etc/pulse/default.pa
cp /etc/pulse/default.pa /etc/pulse/system.pa

/usr/sbin/usermod -G pulse-access root
/usr/sbin/usermod -a -G audio pulse

# pulseaudio settings for bluetooth a2dp_sink
sed -i '/<allow own="org.pulseaudio.Server"\/>/a \ \ \ \ <allow send_destination="org.bluez"/>' /etc/dbus-1/system.d/pulseaudio-system.conf

%files audio-common
%attr(0644,root,root) /usr/lib/systemd/system/pulseaudio.service
%attr(0644,root,root) /usr/lib/systemd/system/audiosetting.service

###############################################################################
# usb gadget
%package usb-common
Summary:    usb
Group:		System

%description usb-common
usb

%files usb-common
%attr(0755,root,root) /usr/bin/adbd
%attr(0644,root,root) /usr/lib/systemd/system/adbd.service
%attr(0644,root,root) /usr/lib/systemd/system/rndis.service
%attr(0644,root,root) /etc/udev/rules.d/99-adb-restart.rules
