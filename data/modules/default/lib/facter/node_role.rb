# node_role.rb
require 'facter'
Facter.add(:node_role) do
   confine :kernel => 'Linux'
      setcode do
        Facter::Core::Execution.exec('cat /etc/.role/role')
      end
end
