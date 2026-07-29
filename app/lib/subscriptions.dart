import 'package:flutter/foundation.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'package:purchases_ui_flutter/purchases_ui_flutter.dart';

import 'config.dart';

/// Everything the app knows about paid access.
///
/// RevenueCat answers one question — *does this user have Pro?* — and owns the
/// purchase, receipt and renewal handling. It does **not** enforce the free
/// tier: the server does that, keyed on [userId].
class Subscriptions {
  static Future<void> init() async {
    await Purchases.setLogLevel(kDebugMode ? LogLevel.debug : LogLevel.warn);
    await Purchases.configure(
      PurchasesConfiguration(AppConfig.revenueCatApiKey),
    );

    if (kDebugMode) {
      // The entitlement identifier must match the dashboard exactly; printing
      // what the SDK actually returns makes a mismatch obvious immediately.
      final info = await Purchases.getCustomerInfo();
      debugPrint('RevenueCat user: ${info.originalAppUserId}');
      debugPrint('RevenueCat entitlements: ${info.entitlements.all.keys}');
    }
  }

  /// Anonymous, stable per-install id. The server tracks free-tier usage
  /// against this, so it must be sent with every session request.
  static Future<String> userId() => Purchases.appUserID;

  static Future<bool> isPro() async {
    try {
      final info = await Purchases.getCustomerInfo();
      return info.entitlements.active.containsKey(AppConfig.proEntitlement);
    } catch (e) {
      debugPrint('Could not read entitlements: $e');
      return false; // fail closed — the server enforces the quota anyway
    }
  }

  /// Show the paywall. Returns true if the user came back with Pro.
  static Future<bool> showPaywall() async {
    final result = await RevenueCatUI.presentPaywall(displayCloseButton: true);
    return result == PaywallResult.purchased || result == PaywallResult.restored;
  }
}
