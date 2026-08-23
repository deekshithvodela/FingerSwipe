# Maintainer: Deekshith Vodela <deekshithvodela@gmail.com>
pkgname=fingerswipe-bin
_pkgname=fingerswipe
pkgver=1.2.0
pkgrel=1
pkgdesc="Fluid 3-finger touchpad gesture daemon for PipeWire volume, brightness, and Start Menu"
arch=('x86_64')
url="https://deekshithvodela.github.io/FingerSwipe/"
license=('MIT')
depends=('libinput' 'systemd-libs' 'pipewire' 'python>=3.13')
provides=('fingerswipe')
conflicts=('fingerswipe')
source=("https://github.com/deekshithvodela/FingerSwipe/releases/download/v${pkgver}/fingerswipe-${pkgver}-linux-${arch}.tar.gz")
sha256sums=('SKIP')

package() {
    cd "${srcdir}/fingerswipe-${pkgver}-linux-${arch}"
    install -d "${pkgdir}/usr/lib"
    install -d "${pkgdir}/opt/fingerswipe"
    install -d "${pkgdir}/usr/bin"
    install -d "${pkgdir}/usr/lib/systemd/user"
    install -d "${pkgdir}/usr/lib/udev/rules.d"
    install -d "${pkgdir}/usr/share/licenses/${pkgname}"

    cp -a opt/fingerswipe/* "${pkgdir}/opt/fingerswipe/"
    cp -d usr/lib/libfingerswipe.so* "${pkgdir}/usr/lib/"
    cp usr/lib/systemd/user/fingerswipe.service "${pkgdir}/usr/lib/systemd/user/"
    cp usr/lib/udev/rules.d/99-fingerswipe.rules "${pkgdir}/usr/lib/udev/rules.d/"
    install -m644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"

    ln -s /opt/fingerswipe/bin/fingerswipe "${pkgdir}/usr/bin/fingerswipe"
}
