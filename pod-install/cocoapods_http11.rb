# Forces CocoaPods' CDN client (Typhoeus over libcurl) onto HTTP/1.1.
#
# cocoapods-core's CDNSource hardcodes `http_version: :httpv2_0` and fans many
# podspec fetches out over one multiplexed connection. From the self-hosted
# runner that path fails intermittently against cdn.jsdelivr.net with
# "Error in the HTTP2 framing layer", measured at 5-7 failed fetches per cold
# `pod install --repo-update`, and occasionally (as on 2026-09-16, the day
# AppCheckCore 11.3.2 was published) a single podspec failing every one of
# CocoaPods' own retries, which fails the whole iOS deploy. The same fetches
# over HTTP/1.1 fail zero times. Loaded via RUBYOPT by the pod-install action;
# CocoaPods offers no switch of its own. Prepended so the explicit :httpv2_0
# CocoaPods passes is what gets overridden.
require "typhoeus"

module CocoaPodsHttp11
  def initialize(base_url, options = {})
    super(base_url, options.merge(http_version: :httpv1_1))
  end
end

Typhoeus::Request.prepend(CocoaPodsHttp11)
