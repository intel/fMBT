mkdir -p build-win32
docker build -t fmbt_fedora .
docker run -i -v ${PWD}/build-win32:/build-win32 fmbt_fedora sh << COMMANDS
echo Copying build binaries to host
cp fMBT/build-win32/*.exe /build-win32
cp fMBT/build-win32/*.msi /build-win32
echo Changing owner from \$(id -u):\$(id -g) to $(id -u):$(id -u)
chown -R $(id -u):$(id -u) /build-win32
COMMANDS
