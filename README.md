# firefly
failsafe image for illumos-based distros

How To build failsafe image for OmniOS:

1. Install distribution-constructor.
2. Clone git@github.com:alhazred/firefly.git to /opt/firefly
3. Copy python scripts from the /opt/firefly/distr directory to /usr/lib/python2.6/vendor-packages/solaris_install/distro_const/checkpoints/
4. From the /opt/firefly directory, run "distro_const build -v firefly.xml" 
