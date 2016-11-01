Pod::Spec.new do |s|
  s.name = "GoogleMaps"
  s.version = "2.1.0"
  s.summary = "A short description of GoogleMaps."
  s.description = <<-DESC
  Use the Google Maps SDK for iOS to enrich your app with interactive maps and immersive Street View panoramas.
                   DESC
  s.homepage = "https://developers.google.com/maps/ios/"
  s.license = { :type => "Copyright", :text => "      If you use the Google Maps SDK for iOS in your application, you must\n      include the attribution text as part of a legal notices section in your\n      application. Including legal notices as an independent menu item, or as\n      part of an \"About\" menu item, is recommended.\n\n      You can get the attribution text by making a call to\n      GMSServices.openSourceLicenseInfo().\n" }
  s.author = "Google Inc."
  s.platform = :ios, "8.0"
  s.source = { :http => "https://raw.githubusercontent.com/nebiros/GoogleMapsPodspec/master/GoogleMaps-2.1.0.tar.gz" }
  s.preserve_paths = "CHANGELOG",
    "Example",
    "README.md"
  s.frameworks  = "Accelerate",
    "AVFoundation",
    "CoreBluetooth",
    "CoreData",
    "CoreLocation",
    "CoreText",
    "GLKit",
    "ImageIO",
    "OpenGLES",
    "QuartzCore",
    "Security",
    "SystemConfiguration",
    "CoreGraphics"
  s.libraries   = "icucore",
    "c++",
    "z"
  s.resources = "Subspecs/Maps/Frameworks/GoogleMaps.framework/GoogleMaps.bundle"
  s.vendored_frameworks = "Subspecs/Maps/Frameworks/GoogleMaps.framework"
  s.xcconfig = {
    "OTHER_CODE_SIGN_FLAGS" => "--deep"
  }
end
