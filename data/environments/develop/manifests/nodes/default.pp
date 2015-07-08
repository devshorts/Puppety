node default {
  case $node_role{
    # role-test: roles/slave-test
    'slave': {
      file {'/tmp/node-role': # resource type file and file
        ensure  => present,   # make sure it exists
        mode    => 0644,      # file permissions
        content =>    "Here is my Role ${$node_Role}.\n",  # note the node role
       }
    }
    # role-test: roles/listener-test
    'listener': {
      file { '/tmp/listener': # resource type file and file
        ensure  => present,   # make sure it exists
        mode    => 0644,      # file permissions
        content =>    "I am a listener",  # note the node role
      }
    }
   }
}
