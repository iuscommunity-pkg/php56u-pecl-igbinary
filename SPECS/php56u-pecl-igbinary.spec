# IUS spec file for php56u-pecl-igbinary, forked from:
#
# Fedora spec file for php-pecl-igbinary
#
# Copyright (c) 2010-2014 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/3.0/
#
# Please, preserve the changelog entries
#

%global extname   igbinary
%global with_zts  0%{?__ztsphp:1}
%global ini_name  40-%{extname}.ini
%global php_base  php56u

Summary:        Replacement for the standard PHP serializer
Name:           %{php_base}-pecl-%{extname}
Version:        2.0.0
Release:        1.ius%{?dist}
Source0:        http://pecl.php.net/get/%{extname}-%{version}.tgz
Source1:        igbinary.ini
License:        BSD
Group:          System Environment/Libraries
URL:            http://pecl.php.net/package/igbinary
BuildRequires:  %{php_base}-pear
BuildRequires:  %{php_base}-devel
BuildRequires:  %{php_base}-pecl-apcu-devel >= 3.1.7

Requires(post): %{php_base}-pear
Requires(postun): %{php_base}-pear
Requires:       %{php_base}(zend-abi) = %{php_zend_api}
Requires:       %{php_base}(api) = %{php_core_api}

# provide the stock name
Provides:       php-pecl-%{extname} = %{version}
Provides:       php-pecl-%{extname}%{?_isa} = %{version}

# provide the stock and IUS names without pecl
Provides:       php-%{extname} = %{version}
Provides:       php-%{extname}%{?_isa} = %{version}
Provides:       %{php_base}-%{extname} = %{version}
Provides:       %{php_base}-%{extname}%{?_isa} = %{version}

# provide the stock and IUS names in pecl() format
Provides:       php-pecl(%{extname}) = %{version}
Provides:       php-pecl(%{extname})%{?_isa} = %{version}
Provides:       %{php_base}-pecl(%{extname}) = %{version}
Provides:       %{php_base}-pecl(%{extname})%{?_isa} = %{version}

# conflict with the stock name
Conflicts:      php-pecl-%{extname} < %{version}

%{?filter_provides_in: %filter_provides_in %{php_extdir}/.*\.so$}
%{?filter_provides_in: %filter_provides_in %{php_ztsextdir}/.*\.so$}
%{?filter_setup}


%description
Igbinary is a drop in replacement for the standard PHP serializer.

Instead of time and space consuming textual representation, 
igbinary stores PHP data structures in a compact binary form. 
Savings are significant when using memcached or similar memory
based storages for serialized data.


%package devel
Summary:        Igbinary developer files (header)
Group:          Development/Libraries
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       %{php_base}-devel%{?_isa}

# provide the stock name
Provides:       php-pecl-%{extname}-devel = %{version}
Provides:       php-pecl-%{extname}-devel%{?_isa} = %{version}

# provide the stock and IUS names without pecl
Provides:       php-%{extname}-devel = %{version}
Provides:       php-%{extname}-devel%{?_isa} = %{version}
Provides:       %{php_base}-%{extname}-devel = %{version}
Provides:       %{php_base}-%{extname}-devel%{?_isa} = %{version}

# conflict with the stock name
Conflicts:      php-pecl-%{extname}-devel < %{version}


%description devel
These are the files needed to compile programs using Igbinary


%prep
%setup -q -c

mv %{extname}-%{version} NTS

pushd NTS

# Check version
extver=$(sed -n '/#define PHP_IGBINARY_VERSION/{s/.* "//;s/".*$//;p}' src/php5/igbinary.h)
if test "x${extver}" != "x%{version}%{?prever}"; then
   : Error: Upstream version is ${extver}, expecting %{version}%{?prever}.
   exit 1
fi
popd

%if %{with_zts}
cp -r NTS ZTS
%endif


%build
pushd NTS
%{_bindir}/phpize
%configure --with-php-config=%{_bindir}/php-config
make %{?_smp_mflags}
popd

%if %{with_zts}
pushd ZTS
%{_bindir}/zts-phpize
%configure --with-php-config=%{_bindir}/zts-php-config
make %{?_smp_mflags}
popd
%endif


%install
make install -C NTS INSTALL_ROOT=%{buildroot}

install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{extname}.xml

install -D -m 644 %{SOURCE1} %{buildroot}%{php_inidir}/%{ini_name}

# Install the ZTS stuff
%if %{with_zts}
make install -C ZTS INSTALL_ROOT=%{buildroot}
install -D -m 644 %{SOURCE1} %{buildroot}%{php_ztsinidir}/%{ini_name}
%endif

# Test & Documentation
pushd NTS
for i in $(grep 'role="test"' ../package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 $i %{buildroot}%{pecl_testdir}/%{extname}/tests/$i
done
for i in $(grep 'role="doc"' ../package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 $i %{buildroot}%{pecl_docdir}/%{extname}/$i
done
popd


%check
# drop extension load from phpt
sed -e '/^extension=/d' -i ?TS/tests/*phpt

# APC required for test 045
if [ -f %{php_extdir}/apcu.so ]; then
  MOD="-d extension=apcu.so"
fi

: simple NTS module load test, without APC, as optional
%{__php} --no-php-ini \
    --define extension=%{buildroot}%{php_extdir}/%{extname}.so \
    --modules | grep %{extname}

: upstream test suite
pushd NTS
TEST_PHP_EXECUTABLE=%{__php} \
TEST_PHP_ARGS="-n $MOD -d extension=$PWD/modules/%{extname}.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__php} -n run-tests.php --show-diff
popd

%if %{with_zts}
: simple ZTS module load test, without APC, as optional
%{__ztsphp} --no-php-ini \
    --define extension=%{buildroot}%{php_ztsextdir}/%{extname}.so \
    --modules | grep %{extname}

: upstream test suite
pushd ZTS
TEST_PHP_EXECUTABLE=%{__ztsphp} \
TEST_PHP_ARGS="-n $MOD -d extension=$PWD/modules/%{extname}.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__ztsphp} -n run-tests.php --show-diff
popd
%endif


%post
%{pecl_install} %{pecl_xmldir}/%{extname}.xml >/dev/null || :


%postun
if [ $1 -eq 0 ]; then
    %{pecl_uninstall} %{extname} >/dev/null || :
fi


%files
%doc %{pecl_docdir}/%{extname}
%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/%{extname}.so
%{pecl_xmldir}/%{extname}.xml

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/%{ini_name}
%{php_ztsextdir}/%{extname}.so
%endif


%files devel
%doc %{pecl_testdir}/%{extname}
%{php_incldir}/ext/%{extname}

%if %{with_zts}
%{php_ztsincldir}/ext/%{extname}
%endif


%changelog
* Wed Nov 23 2016 Carl George <carl.george@rackspace.com> - 2.0.0-1.ius
- Latest upstream
- Install package.xml as %%{extname}.xml, not %%{name}.xml
- Clean up provides and conflicts
- Drop extension load from phpt (Fedora)

* Thu Jun 16 2016 Ben Harper <ben.harper@rackspace.com> - 1.2.1-6.ius
- update filters to include zts

* Thu Feb 11 2016 Carl George <carl.george@rackspace.com> - 1.2.1-5.ius
- Remove minimum requirement on %{php_base}-devel, it's implied in the name
- Conflict/provide the stock name in the -devel subpackage
- Clean up miscellaneous provides

* Thu Oct 23 2014 Ben Harper <ben.harper@rackspace.com> - 1.2.1-4.ius
- porting from php55u-pecl-igbinary

* Fri Oct 10 2014 Carl George <carl.george@rackspace.com> - 1.2.1-3.ius
- Directly require the correct pear package, not /usr/bin/pecl
- Conflict with stock package
- Provides the stock package

* Wed Oct 01 2014 Carl George <carl.george@rackspace.com> - 1.2.1-2.ius
- Add numerical prefix to extension configuration file

* Mon Sep 29 2014 Carl George <carl.george@rackspace.com> - 1.2.1-1.ius
- Port to IUS
- Change ini file from here document to separate source

* Fri Aug 29 2014 Remi Collet <remi@fedoraproject.org> - 1.2.1-1
- Update to 1.2.1

* Thu Aug 28 2014 Remi Collet <remi@fedoraproject.org> - 1.2.0-1
- update to 1.2.0
- open https://github.com/igbinary/igbinary/pull/36

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.2-0.12.gitc35d48f
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Jun 19 2014 Remi Collet <rcollet@redhat.com> - 1.1.2-0.11.gitc35d48f
- rebuild for https://fedoraproject.org/wiki/Changes/Php56

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.2-0.10.gitc35d48f
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed Apr 23 2014 Remi Collet <rcollet@redhat.com> - 1.1.2-0.9.gitc35d48f
- add numerical prefix to extension configuration file

* Mon Mar 10 2014 Remi Collet <rcollet@redhat.com> - 1.1.2-0.8.gitc35d48f
- cleanups and drop SCL support
- install doc in pecl_docdir
- install tests in pecl_testdir (devel)

* Mon Jul 29 2013 Remi Collet <rcollet@redhat.com> - 1.1.2-0.7.gitc35d48f
- adapt for scl

* Sat Jul 27 2013 Remi Collet <remi@fedoraproject.org> - 1.1.2-0.6.gitc35d48f
- latest snapshot
- fix build with APCu
- spec cleanups

* Fri Mar 22 2013 Remi Collet <rcollet@redhat.com> - 1.1.2-0.5.git3b8ab7e
- rebuild for http://fedoraproject.org/wiki/Features/Php55

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.2-0.4.git3b8ab7e
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.2-0.3.git3b8ab7e
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Apr 23 2012 Collet <remi@fedoraproject.org> - 1.1.2-0.2.git3b8ab7e
- enable ZTS extension

* Fri Jan 20 2012 Collet <remi@fedoraproject.org> - 1.1.2-0.1.git3b8ab7e
- update to git snapshot for php 5.4

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Sun Sep 18 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-3
- fix EPEL-6 build, no arch version for php-devel

* Sat Sep 17 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-2
- clean spec, adapted filters

* Mon Mar 14 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-1
- version 1.1.1 published on pecl.php.net
- rename to php-pecl-igbinary

* Mon Jan 17 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-1
- update to 1.1.1

* Fri Dec 31 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-3
- updated tests from Git.

* Sat Oct 23 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-2
- filter provides to avoid igbinary.so
- add missing %%dist

* Wed Sep 29 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-1
- initital RPM

