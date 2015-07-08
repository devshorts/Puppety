FROM centos:centos7

RUN rpm -ivh http://yum.puppetlabs.com/puppetlabs-release-el-7.noarch.rpm
RUN yum -y install puppet-server
RUN yum -y install epel-release
RUN yum -y install python-pip && pip install pytest

COPY data/ /etc/puppet/

# overrides
ADD autosign.conf /etc/puppet/autosign.conf
ADD entrypoint.templated /entrypoint
RUN chmod +x /entrypoint
ADD runners /root/test-runners

ENTRYPOINT ["/entrypoint"]
