# node-test:  nodes/random-test
node /random/ {
  file {'/tmp/node-random':   # resource type file and f
    ensure  => present, # make sure it exists
    mode    => 0644,    # file permissions
    content =>   "Here is my Public IP Address: ${ipaddress_eth0}.\n",  # note the ipaddress_eth0
   }
 }
