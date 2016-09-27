# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "ubuntu/trusty64"

  # Enable NFS access to the disk
  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.synced_folder ".", "/vagrant/mapit", :nfs => true

  # NFS requires a host-only network
  # This also allows you to test via other devices (e.g. mobiles) on the same
  # network
  config.vm.network :private_network, ip: "10.11.12.13"

  # Django dev server
  config.vm.network "forwarded_port", guest: 8000, host: 8000

  # Give the VM a bit more power to speed things up
  config.vm.provider "virtualbox" do |v|
    v.memory = 2048
    v.cpus = 2
  end

  # Provision the vagrant box
  config.vm.provision "shell", inline: <<-SHELL
    apt-get update

    chown vagrant:vagrant /vagrant
    cd /vagrant/mapit

    # Install the packages from conf/packages.ubuntu-trusty
    xargs apt-get install -qq -y < conf/packages.ubuntu-trusty

    # Create a postgresql user
    su postgres -c 'psql -c "CREATE USER vagrant SUPERUSER CREATEDB"'

    # Run install-as-user to set up a database, virtualenv, python, sass etc
    su vagrant -c 'bin/install-as-user vagrant mapit.mysociety.org /vagrant'

    # Nicer running of runserver
    su vagrant -c '../virtualenv-mapit/bin/pip install pyinotify'

    # Auto-activate virtualenv on login
    echo >> /home/vagrant/.bashrc "source /vagrant/virtualenv-mapit/bin/activate"
  SHELL

end
