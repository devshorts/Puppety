FROM centos:centos7

RUN rpm -ivh https://yum.puppetlabs.com/puppetlabs-release-el-7.noarch.rpm
RUN yum -y install epel-release
RUN yum -y install puppet
RUN yum -y install python-pip && pip install pytest
#RUN yum -y install iptables ca-certificates lxc e2fsprogs docker-io

ADD puppet.conf.templated /etc/puppet/puppet.conf
ADD runners /root/test-runners
ADD entrypoint.templated /root/runner

RUN chmod +x /root/runner

COPY data /

ENTRYPOINT ["/root/runner"]
