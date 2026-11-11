Name:		xslthl
Version:	2.1.3
Release:	1
Summary:	XSLT syntax highlighting extension
Group:		Development/Java
License:	Zlib
URL:		https://github.com/xmlark/xslthl
# Commit 9d6b819014bd3f55ae01e5b6961e8b52b22919ff, the 2.1.3 preparation.
# plugins.jar is removed from the lookaside archive. Saxon connectors are
# not compiled: cooker has no Saxon. The catalog pin 2.0.1 is not strict.
Source0:	xslthl-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(xalan:xalan)

%description
Syntax highlighting for DocBook and other XSLT pipelines. Version 2.1.3
keeps the 2.0 Config and ConnectorXalan API the Gradle documentation
build uses. Saxon 6, Saxon-B, and Saxon-EE connectors are omitted.

%prep
%autosetup -n xslthl-%{version}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete
sed -i 's/\r$//' CHANGES.txt LICENSE.txt

%build
set -eo pipefail
find src/main/java -name '*.java' \
	! -name ConnectorSaxon6.java \
	! -name ConnectorSaxonB.java \
	! -name ConnectorSaxonEE.java \
	> sources.list
test "$(wc -l < sources.list)" -eq 28
mkdir -p classes
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp %{_javadir}/xalan.jar:%{_javadir}/serializer.jar \
	-d classes @sources.list
/bin/cp -a highlighters/. classes/
cat > manifest.mf << 'EOF'
Manifest-Version: 1.0
Automatic-Module-Name: net.sf.xslthl

EOF
jar cfm xslthl.jar manifest.mf -C classes .
jar i xslthl.jar
javap -verbose -cp xslthl.jar net.sf.xslthl.Config | grep -F 'major version: 52'
jar --describe-module --file xslthl.jar > describe.txt
if grep -F -q 'Unable to derive' describe.txt; then
	cat describe.txt
	exit 1
fi

cat > xslthl.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>net.sf.xslthl</groupId>
  <artifactId>xslthl</artifactId>
  <version>2.1.3</version>
  <name>XSLTHL</name>
  <description>XSLT syntax highlighting extension</description>
  <url>https://github.com/xmlark/xslthl</url>
  <licenses>
    <license>
      <name>zlib License</name>
      <url>https://spdx.org/licenses/Zlib.html</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>xalan</groupId>
      <artifactId>xalan</artifactId>
      <version>2.7.3</version>
      <optional>true</optional>
    </dependency>
  </dependencies>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact xslthl.pom:xslthl.jar \
	--file-name xslthl \
	--filelist .mfiles

%check
set -eo pipefail
JAR=%{buildroot}%{_javadir}/xslthl.jar
test -f "$JAR"
rm -rf check
mkdir -p check/hl
( cd check/hl && jar xf "$JAR" )
cat > check/Check.java << 'EOF'
import java.util.List;
import net.sf.xslthl.Block;
import net.sf.xslthl.Config;
import net.sf.xslthl.MainHighlighter;
public class Check {
	public static void main(String[] args) {
		Config cfg = Config.getInstance(args[0]);
		MainHighlighter javaHl = cfg.getMainHighlighter("java");
		List<Block> blocks = javaHl.highlight("int gradle = 1;");
		int styled = 0;
		for (Block block : blocks) {
			if (block.isStyled()) {
				styled++;
			}
		}
		System.out.println("xslthl_ok " + javaHl.getId() + " " + blocks.size() + " styled " + styled);
	}
}
EOF
javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$JAR" -d check check/Check.java
CFG=file://$(pwd)/check/hl/xslthl-config.xml
java -cp "check:$JAR" Check "$CFG" > check/check.log
cat check/check.log
grep -F -q 'xslthl_ok java' check/check.log
grep -E -q 'styled [1-9]' check/check.log

%files -f .mfiles
%license LICENSE.txt
%doc CHANGES.txt
