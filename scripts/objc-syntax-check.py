#!/usr/bin/env python3
"""Generate a stub SDK good enough to type-check the app's changed sources.

This does NOT prove the code links or behaves; it proves the parts that a
compiler alone can catch: undeclared selectors, unknown constants, wrong
argument counts, misuse of nullable/ARC ownership, and malformed control flow.
The real gate is xcodebuild; this is what can run when macOS is unavailable.

The stub is generated rather than written by hand so that adding a symbol is a
one-line change, and so the list of things the file actually depends on stays
visible in review.

    scripts/objc-syntax-check.py app/DSHRootViewController.m [--tree <dir>]
"""
import argparse
import os
import sys

# Framework headers a file may `#import <Framework/Header.h>`; all resolve to
# the single stub, because the stub is permissive by design.
HEADERS = [
    "Foundation/Foundation.h", "UIKit/UIKit.h", "WebKit/WebKit.h",
    "CoreGraphics/CoreGraphics.h", "QuartzCore/QuartzCore.h",
    "objc/runtime.h", "os/log.h",
]

STUB = r"""
#ifndef DSH_STUB_SDK_H
#define DSH_STUB_SDK_H
#include <stddef.h>
#include <stdint.h>

/* ── scalar and macro layer ─────────────────────────────────────────── */
typedef const struct __CFString *CFStringRef;
typedef signed char BOOL;
#define YES ((BOOL)1)
#define NO ((BOOL)0)
#define nil ((id)0)
typedef long NSInteger;
typedef unsigned long NSUInteger;
typedef double CGFloat;
typedef double NSTimeInterval;
#define NS_ENUM(t, n) t n; enum
#define NS_OPTIONS(t, n) t n; enum
#define NS_ASSUME_NONNULL_BEGIN
#define NS_ASSUME_NONNULL_END
#define API_AVAILABLE(...)
#define API_DEPRECATED(...)
#define NS_SWIFT_NAME(x)
#define NS_SWIFT_UNAVAILABLE(x)
#define NS_DESIGNATED_INITIALIZER
#define NS_UNAVAILABLE
#define NS_REQUIRES_SUPER
#define NS_REFINED_FOR_SWIFT
#define NS_RETURNS_RETAINED
#define NS_RETURNS_NOT_RETAINED
#define __kindof
typedef CFStringRef CFStringRefConst;
#define IBOutlet
#define IBAction void

typedef struct { CGFloat x, y; } CGPoint;
typedef struct { CGFloat width, height; } CGSize;
typedef struct { CGPoint origin; CGSize size; } CGRect;
typedef struct { CGFloat top, leading, bottom, trailing; } NSDirectionalEdgeInsets;
static inline NSDirectionalEdgeInsets NSDirectionalEdgeInsetsMake(CGFloat t, CGFloat l, CGFloat b, CGFloat r) {
    NSDirectionalEdgeInsets i = {t, l, b, r}; return i;
}
static inline CGRect CGRectMake(CGFloat x, CGFloat y, CGFloat w, CGFloat h) {
    CGRect r = {{x, y}, {w, h}}; return r;
}


extern const CGRect CGRectZero;
extern const CGRect CGRectNull;
typedef void (^dispatch_block_t)(void);
typedef unsigned long dispatch_time_t;
static const dispatch_time_t DISPATCH_TIME_NOW = 0;
static const unsigned long NSEC_PER_SEC = 1000000000ul;
dispatch_time_t dispatch_time(dispatch_time_t when, long delta);
void dispatch_after(dispatch_time_t when, id queue, dispatch_block_t block);
extern id dispatch_get_main_queue(void);
typedef NSUInteger UIKeyModifierFlags;
static const UIKeyModifierFlags UIKeyModifierCommand = 1 << 20;
static const UIKeyModifierFlags UIKeyModifierShift = 1 << 17;
static const UIKeyModifierFlags UIKeyModifierAlternate = 1 << 19;
static const UIKeyModifierFlags UIKeyModifierControl = 1 << 18;
typedef NSUInteger UIDeviceBatteryState;

/* Option sets and enums, all plain integer typedefs plus constants. */
typedef NSInteger WKNavigationActionPolicy;
enum { WKNavigationActionPolicyCancel = 0, WKNavigationActionPolicyAllow = 1 };
typedef NSInteger WKNavigationResponsePolicy;
enum { WKNavigationResponsePolicyCancel = 0, WKNavigationResponsePolicyAllow = 1, WKNavigationResponsePolicyDownload = 2 };
typedef NSInteger UIStatusBarStyle;
enum { UIStatusBarStyleDefault = 0, UIStatusBarStyleLightContent = 1 };
typedef NSUInteger UILayoutConstraintAxis;
enum { UILayoutConstraintAxisHorizontal = 0, UILayoutConstraintAxisVertical = 1 };
typedef NSInteger UIStackViewAlignment;
enum { UIStackViewAlignmentCenter = 3 };
typedef NSUInteger UIControlEvents;
enum { UIControlEventTouchUpInside = 1 << 6 };
typedef NSInteger UIModalPresentationStyle;
enum { UIModalPresentationPageSheet = 1, UIModalPresentationAutomatic = -2 };
typedef NSUInteger UIMenuElementAttributes;
enum { UIMenuElementAttributesDestructive = 1 << 1 };
typedef NSUInteger UIMenuOptions;
enum { UIMenuOptionsDisplayInline = 1 << 0 };
typedef NSUInteger UIPopoverArrowDirection;
enum { UIPopoverArrowDirectionUp = 1 << 1 };
typedef NSInteger UIUserInterfaceIdiom;
enum { UIUserInterfaceIdiomPhone = 0, UIUserInterfaceIdiomPad = 1 };
typedef NSInteger UIAlertControllerStyle;
enum { UIAlertControllerStyleActionSheet = 0, UIAlertControllerStyleAlert = 1 };
typedef NSInteger UIAlertActionStyle;
enum { UIAlertActionStyleDefault = 0, UIAlertActionStyleCancel = 1, UIAlertActionStyleDestructive = 2 };
typedef NSInteger UIImageSymbolWeight;
enum { UIImageSymbolWeightMedium = 3 };
typedef CGFloat UIFontWeight;
static const UIFontWeight UIFontWeightSemibold = 0.3;
static const UIFontWeight UIFontWeightRegular = 0.0;
static const UIFontWeight UIFontWeightBold = 0.4;
typedef NSUInteger NSURLRequestCachePolicy;
enum { NSURLRequestReloadIgnoringLocalCacheData = 1 };
typedef NSInteger UIScrollViewContentInsetAdjustmentBehavior;
enum { UIScrollViewContentInsetAdjustmentNever = 3 };
typedef NSInteger UIStackViewDistribution;
enum { UIStackViewDistributionFill = 0 };
typedef NSInteger NSTextAlignment;
enum { NSTextAlignmentLeft = 0, NSTextAlignmentCenter = 1 };
typedef NSInteger NSLineBreakMode;
enum { NSLineBreakByTruncatingTail = 4 };
typedef NSUInteger NSDirectoryEnumerationOptions;

/* Forward declarations. Every class a header names before its definition. */
@class NSString, NSArray, NSDictionary, NSData, NSURL, NSURLRequest, NSURLResponse;
@class NSNotification, NSNotificationCenter, NSFileManager, NSUserDefaults, NSBundle;
@class UIImage, UIColor, UIFont, UIView, UIViewController, UIButton, UILabel;
@class UIMenu, UIAction, UIAlertController, UIAlertAction, UIGestureRecognizer, UIWindow;
@class UIScreen, UIApplication, UIDevice, NSLayoutConstraint, NSValue, NSDate, NSError;
@class UIMenuElement, UIKeyCommand, UIScrollView, WKWebView, WKNavigation, WKDownload;
@class UINavigationItem, UIBarButtonItem, UISheetPresentationController;
@class UIPopoverPresentationController, UIButtonConfiguration, UIStackView;
@class WKWebViewConfiguration, WKWindowFeatures, WKNavigationAction, WKNavigationResponse;
@class WKWebsiteDataStore, WKWebpagePreferences, WKFrameInfo, UISceneSession, UIScene, NSCoder, NSIndexPath, UITableView;
@class UITableViewCell, NSUUID, UITableViewController, UILayoutGuide, NSLayoutAnchor;
typedef NSString *NSNotificationName;
extern const CFStringRef kCFBundleVersionKey;
extern const CFStringRef kCFBundleShortVersionStringKey;


/* ── Foundation ─────────────────────────────────────────────────────── */
@protocol NSObject
- (BOOL)respondsToSelector:(SEL)s;
- (BOOL)isKindOfClass:(Class)c;
@property (readonly) Class class;
@end
__attribute__((objc_root_class))
@interface NSObject <NSObject>
+ (instancetype)alloc;
+ (instancetype)new;
- (instancetype)init;
- (id)copy;
- (BOOL)isEqual:(id)o;
- (void)performSelector:(SEL)s withObject:(id)o afterDelay:(NSTimeInterval)d;
+ (void)cancelPreviousPerformRequestsWithTarget:(id)t selector:(SEL)s object:(id)o;
+ (void)cancelPreviousPerformRequestsWithTarget:(id)t;
@end
@interface NSNumber : NSObject
+ (instancetype)numberWithDouble:(double)d;
+ (instancetype)numberWithInt:(int)i;
@property (readonly) double doubleValue;
@end
@interface NSUUID : NSObject @end
@interface NSValue : NSObject
+ (instancetype)valueWithNonretainedObject:(id)o;
@end
@interface NSString : NSObject
+ (instancetype)stringWithFormat:(NSString *)f, ...;
+ (instancetype)stringWithUTF8String:(const char *)s;
@property (readonly) NSUInteger length;
@property (readonly) const char *UTF8String;
@property (readonly) double doubleValue;
- (BOOL)isEqualToString:(NSString *)o;
- (BOOL)hasPrefix:(NSString *)p;
- (BOOL)hasSuffix:(NSString *)p;
- (BOOL)containsString:(NSString *)s;
@property (readonly) NSString *lowercaseString;
@property (readonly) NSString *stringByDeletingPathExtension;
@property (readonly) NSString *pathExtension;
@end
@interface NSArray<T> : NSObject
+ (instancetype)arrayWithObjects:(const T[])o count:(NSUInteger)c;
@property (readonly) NSUInteger count;
- (T)objectAtIndexedSubscript:(NSUInteger)i;
- (T)firstObject;
+ (instancetype)arrayWithObjects:(id)first, ...;
@end
@interface NSMutableArray<T> : NSArray<T>
+ (instancetype)array;
+ (instancetype)arrayWithCapacity:(NSUInteger)c;
- (void)addObject:(T)o;
- (void)addObjectsFromArray:(NSArray<T> *)o;
@end
@interface NSDictionary<K, V> : NSObject
- (V)objectForKeyedSubscript:(K)k;
+ (instancetype)dictionaryWithObjects:(const id [])o forKeys:(const id [])k count:(NSUInteger)c;
@end
@interface NSMutableDictionary<K, V> : NSDictionary<K, V>
+ (instancetype)dictionary;
- (void)setObject:(V)o forKeyedSubscript:(K)k;
- (void)removeObjectForKey:(K)k;
@end
@interface NSMutableString : NSObject
@end
@interface NSURL : NSObject
- (NSArray<NSString *> *)pathComponents;
- (NSURL *)URLByAppendingPathComponent:(NSString *)p;
- (NSURL *)URLByAppendingPathComponent:(NSString *)p isDirectory:(BOOL)d;
- (NSString *)lastPathComponent;
+ (instancetype)URLWithString:(NSString *)s;
@property (readonly) NSString *absoluteString;
@property (readonly) NSString *host;
@property (readonly) NSNumber *port;
@property (readonly) NSString *scheme;
@property (readonly) NSString *path;
@end
@interface NSData : NSObject @end
@interface NSURLRequest : NSObject
@property (readonly) NSURL *URL;
+ (instancetype)requestWithURL:(NSURL *)u;
- (instancetype)initWithURL:(NSURL *)u;
@end
@interface NSMutableURLRequest : NSURLRequest
@property NSURLRequestCachePolicy cachePolicy;
- (void)setValue:(NSString *)v forHTTPHeaderField:(NSString *)f;
@end
@interface NSURLResponse : NSObject @end
@interface NSHTTPURLResponse : NSURLResponse
@property (readonly) NSInteger statusCode;
@property (readonly) NSDictionary *allHeaderFields;
@property (readonly) NSURL *URL;
- (BOOL)isKindOfClass:(Class)c;
@property (readonly) Class class;
@end
@interface NSError : NSObject
@property (readonly) NSInteger code;
@property (readonly) NSString *localizedDescription;
@end
@interface NSNotification : NSObject
@property (readonly) NSString *name;
@property (readonly) NSDictionary *userInfo;
@property (readonly) id object;
@end
@interface NSNotificationCenter : NSObject
+ (instancetype)defaultCenter;
- (void)addObserver:(id)o selector:(SEL)s name:(NSString *)n object:(id)obj;
- (void)removeObserver:(id)o;
- (void)postNotificationName:(NSString *)n object:(id)o;
@end
@interface NSBundle : NSObject
+ (instancetype)mainBundle;
- (id)objectForInfoDictionaryKey:(NSString *)k;
- (id)objectForInfoDictionaryKeyCF:(CFStringRef)k;
@end
@interface NSUserDefaults : NSObject
+ (instancetype)standardUserDefaults;
- (id)objectForKey:(NSString *)k;
- (void)setObject:(id)v forKey:(NSString *)k;
- (BOOL)boolForKey:(NSString *)k;
- (void)setInteger:(NSInteger)v forKey:(NSString *)k;
- (NSInteger)integerForKey:(NSString *)k;
- (void)setBool:(BOOL)v forKey:(NSString *)k;
@end
@interface NSFileManager : NSObject
+ (instancetype)defaultManager;
- (NSArray<NSURL *> *)URLsForDirectory:(NSUInteger)d inDomains:(NSUInteger)m;
- (BOOL)createDirectoryAtURL:(NSURL *)u withIntermediateDirectories:(BOOL)i attributes:(NSDictionary *)a error:(NSError **)e;
- (BOOL)fileExistsAtPath:(NSString *)p;
- (BOOL)createFileAtPath:(NSString *)p contents:(NSData *)d attributes:(NSDictionary *)a;
- (BOOL)removeItemAtURL:(NSURL *)u error:(NSError **)e;
@end
@interface NSDate : NSObject
+ (instancetype)date;
@property (readonly) NSTimeInterval timeIntervalSinceNow;
@property (readonly) NSTimeInterval timeIntervalSince1970;
@end
@interface NSCoder : NSObject @end
@interface NSLocale : NSObject
+ (instancetype)localeWithLocaleIdentifier:(NSString *)i;
@end
@interface NSTimeZone : NSObject
+ (instancetype)systemTimeZone;
+ (instancetype)timeZoneWithAbbreviation:(NSString *)a;
@end
@interface NSDateFormatter : NSObject
+ (instancetype)new2;
- (instancetype)init;
@property (copy) NSString *dateFormat;
@property (strong) NSLocale *locale;
@property (strong) NSTimeZone *timeZone;
- (NSString *)stringFromDate:(NSDate *)d;
@end
@interface NSFileHandle : NSObject
+ (instancetype)fileHandleForWritingAtPath:(NSString *)p;
+ (instancetype)fileHandleForReadingAtPath:(NSString *)p;
- (void)seekToEndOfFile;
- (void)writeData:(NSData *)d;
- (void)synchronizeFile;
- (NSData *)readDataToEndOfFile;
@end
@interface NSData (Bytes)
- (const void *)bytes;
@property (readonly) NSUInteger length;
@end
@interface NSString (Conversion)
- (NSData *)dataUsingEncoding:(NSUInteger)e;
@end
@interface NSIndexPath : NSObject @end
@interface NSLayoutConstraint : NSObject
+ (void)activateConstraints:(NSArray<NSLayoutConstraint *> *)c;
@end
@interface NSLayoutAnchor : NSObject
- (NSLayoutConstraint *)constraintEqualToConstant:(CGFloat)c;
- (NSLayoutConstraint *)constraintEqualToAnchor:(NSLayoutAnchor *)a;
- (NSLayoutConstraint *)constraintEqualToAnchor:(NSLayoutAnchor *)a constant:(CGFloat)c;
- (NSLayoutConstraint *)constraintGreaterThanOrEqualToAnchor:(NSLayoutAnchor *)a;
@end
@interface NSLayoutDimension : NSLayoutAnchor
- (NSLayoutConstraint *)constraintEqualToConstant:(CGFloat)c;
@end
@interface UILayoutGuide : NSObject
@property (readonly) NSLayoutAnchor *leadingAnchor;
@property (readonly) NSLayoutAnchor *trailingAnchor;
@property (readonly) NSLayoutAnchor *topAnchor;
@property (readonly) NSLayoutAnchor *bottomAnchor;
@property (readonly) NSLayoutAnchor *centerXAnchor;
@property (readonly) NSLayoutAnchor *centerYAnchor;
@property (readonly) NSLayoutDimension *widthAnchor;
@property (readonly) NSLayoutDimension *heightAnchor;
@end

/* ── UIKit ──────────────────────────────────────────────────────────── */
@interface UIResponder : NSObject @end
@protocol UIApplicationDelegate <NSObject> @end
@interface UIColor : NSObject
+ (instancetype)systemBackgroundColor;
+ (instancetype)secondaryLabelColor;
+ (instancetype)systemOrangeColor;
+ (instancetype)labelColor;
+ (instancetype)clearColor;
+ (instancetype)blackColor;
+ (instancetype)whiteColor;
+ (instancetype)systemGrayColor;
+ (instancetype)separatorColor;
+ (instancetype)systemGreenColor;
+ (instancetype)systemRedColor;
+ (instancetype)secondarySystemBackgroundColor;
+ (instancetype)tertiaryLabelColor;
+ (instancetype)colorNamed:(NSString *)n;
@end
@interface UIImage : NSObject
+ (instancetype)systemImageNamed:(NSString *)n;
+ (instancetype)systemImageNamed:(NSString *)n withConfiguration:(id)c;
@end
@interface UIImageSymbolConfiguration : NSObject
+ (instancetype)configurationWithPointSize:(CGFloat)p weight:(UIImageSymbolWeight)w;
@end
@interface UIFont : NSObject
+ (instancetype)systemFontOfSize:(CGFloat)s weight:(CGFloat)w;
+ (instancetype)monospacedSystemFontOfSize:(CGFloat)s weight:(CGFloat)w;
+ (instancetype)boldSystemFontOfSize:(CGFloat)s;
@end
@interface UIGestureRecognizer : NSObject @end
@interface UITapGestureRecognizer : UIGestureRecognizer
- (instancetype)initWithTarget:(id)t action:(SEL)a;
@end

@class CALayer;
@interface CALayer : NSObject
@property CGFloat cornerRadius;
@property CGFloat borderWidth;
@property (strong) id borderColor;
@property BOOL masksToBounds;
@end
@interface UIView : UIResponder
- (instancetype)initWithFrame:(CGRect)f;
+ (void)animateWithDuration:(NSTimeInterval)d animations:(void (^)(void))a;
+ (void)animateWithDuration:(NSTimeInterval)d animations:(void (^)(void))a completion:(void (^)(BOOL))c;
@property CGRect frame;
@property CGRect bounds;
@property (copy) UIColor *backgroundColor;
@property (copy) UIColor *tintColor;
@property CGFloat alpha;
@property BOOL translatesAutoresizingMaskIntoConstraints;
@property (getter=isHidden) BOOL hidden;
@property (getter=isOpaque) BOOL opaque;
@property (readonly) CALayer *layer;
@property BOOL isAccessibilityElement;
@property (copy) NSString *accessibilityValue;
@property (copy) NSString *accessibilityHint;
@property BOOL userInteractionEnabled;
@property (copy) NSString *accessibilityLabel;
@property (copy) NSString *accessibilityIdentifier;
@property (readonly) UILayoutGuide *layoutGuide;
@property (readonly) UILayoutGuide *safeAreaLayoutGuide;
@property (readonly) UILayoutGuide *keyboardLayoutGuide;
@property (readonly) NSLayoutAnchor *leadingAnchor;
@property (readonly) NSLayoutAnchor *trailingAnchor;
@property (readonly) NSLayoutAnchor *topAnchor;
@property (readonly) NSLayoutAnchor *bottomAnchor;
@property (readonly) NSLayoutAnchor *centerXAnchor;
@property (readonly) NSLayoutDimension *widthAnchor;
@property (readonly) NSLayoutDimension *heightAnchor;
- (void)addSubview:(UIView *)v;
- (void)addGestureRecognizer:(UIGestureRecognizer *)g;
- (void)layoutIfNeeded;
@end
@interface UIScrollView : UIView
@property UIScrollViewContentInsetAdjustmentBehavior contentInsetAdjustmentBehavior;
@property BOOL bounces;
@property BOOL alwaysBounceVertical;
@property NSDirectionalEdgeInsets directionalLockEnabled2;
@property BOOL scrollEnabled;
@property BOOL showsVerticalScrollIndicator;
@property BOOL keyboardDismissMode2;
@end
@interface UINavigationItem : NSObject
@property (strong) UIBarButtonItem *rightBarButtonItem;
@end
@interface UIBarButtonItem : NSObject
- (instancetype)initWithBarButtonSystemItem:(NSInteger)i target:(id)t action:(SEL)a;
@end
@interface UISheetPresentationController : NSObject
@property (copy) NSArray *detents;
@property BOOL prefersGrabberVisible;
@end
@interface UISheetPresentationControllerDetent : NSObject
+ (instancetype)largeDetent;
@end
@interface UIPopoverPresentationController : NSObject
@property (strong) UIView *sourceView;
@property CGRect sourceRect;
@property (strong) UIBarButtonItem *barButtonItem;
@property UIPopoverArrowDirection permittedArrowDirections;
@end
@interface UIViewController : UIResponder
@property (copy) NSString *title;
@property (readonly) UIView *view;
@property (readonly) UIViewController *presentingViewController;
@property (readonly) UIViewController *presentedViewController;
@property (readonly) BOOL isBeingDismissed;
@property (readonly) UINavigationItem *navigationItem;
@property UIModalPresentationStyle modalPresentationStyle;
@property (readonly) UISheetPresentationController *sheetPresentationController;
@property (readonly) UIPopoverPresentationController *popoverPresentationController;
- (void)viewDidLoad;
- (void)viewWillAppear:(BOOL)a;
- (void)viewDidAppear:(BOOL)a;
- (void)viewWillDisappear:(BOOL)a;
- (void)presentViewController:(UIViewController *)v animated:(BOOL)a completion:(void (^)(void))c;
- (void)dismissViewControllerAnimated:(BOOL)a completion:(void (^)(void))c;
@end
@interface UITableViewController : UIViewController
- (instancetype)initWithStyle:(NSInteger)style;
@property (readonly) UITableView *tableView;
@end
@interface UITableView : UIView
- (void)reloadData;
@end
@interface UITableViewCell : UIView @end
@interface UINavigationController : UIViewController
- (instancetype)initWithRootViewController:(UIViewController *)v;
@end
@interface UIButtonConfiguration : NSObject
+ (instancetype)plainButtonConfiguration;
@property (strong) UIImage *image;
@property NSDirectionalEdgeInsets contentInsets;
@property (strong) UIColor *baseForegroundColor;
@end
@interface UIButton : UIView
+ (instancetype)buttonWithConfiguration:(UIButtonConfiguration *)c primaryAction:(id)a;
@property (getter=isEnabled) BOOL enabled;
- (void)addTarget:(id)t action:(SEL)a forControlEvents:(UIControlEvents)e;
@property BOOL showsMenuAsPrimaryAction;
@property (strong) UIMenu *menu;
@end
@interface UITextField : UIView
@property (copy) NSString *text;
@property (copy) NSString *placeholder;
@end
@interface UILabel : UIView
@property (copy) NSString *text;
@property (strong) UIFont *font;
@property (strong) UIColor *textColor;
@property NSInteger numberOfLines;
@property NSTextAlignment textAlignment;
@property NSLineBreakMode lineBreakMode;
@end
@interface UIStackView : UIView
- (instancetype)initWithArrangedSubviews:(NSArray<UIView *> *)v;
@property UILayoutConstraintAxis axis;
@property UIStackViewAlignment alignment;
@property CGFloat spacing;
@end
@interface UIMenuElement : NSObject @end
@interface UIMenu : UIMenuElement
+ (instancetype)menuWithChildren:(NSArray<UIMenuElement *> *)c;
+ (instancetype)menuWithTitle:(NSString *)t image:(UIImage *)i identifier:(NSString *)id options:(UIMenuOptions)o children:(NSArray<UIMenuElement *> *)c;
@end
@interface UIAction : UIMenuElement
+ (instancetype)actionWithTitle:(NSString *)t image:(UIImage *)i identifier:(NSString *)id handler:(void (^)(UIAction *))h;
@property UIMenuElementAttributes attributes;

@end
@interface UIAlertAction : NSObject
+ (instancetype)actionWithTitle:(NSString *)t style:(UIAlertActionStyle)s handler:(void (^)(UIAlertAction *))h;
@end
@interface UIAlertController : UIViewController
+ (instancetype)alertControllerWithTitle:(NSString *)t message:(NSString *)m preferredStyle:(UIAlertControllerStyle)s;
- (void)addAction:(UIAlertAction *)a;
- (void)addTextFieldWithConfigurationHandler:(void (^)(UITextField *))handler;
@property (readonly) NSArray<UITextField *> *textFields;
@end
@interface UIKeyCommand : UIMenuElement
+ (instancetype)keyCommandWithInput:(NSString *)i modifierFlags:(UIKeyModifierFlags)f action:(SEL)a;
@property (copy) NSString *discoverabilityTitle;
@end
@interface UIDevice : NSObject
+ (instancetype)currentDevice;
@property (readonly) UIUserInterfaceIdiom userInterfaceIdiom;
@property (readonly) NSInteger systemMajorVersion;
@end
@interface UIApplication : UIResponder
+ (instancetype)sharedApplication;
- (void)openURL:(NSURL *)u options:(NSDictionary *)o completionHandler:(void (^)(BOOL))h;
@end
@interface UIWindow : UIView @end
@interface UIScreen : NSObject
+ (instancetype)mainScreen;
@end
@interface UISceneSession : NSObject @end
@interface UIScene : NSObject @end
@interface UIActivityViewController : UIViewController
- (instancetype)initWithActivityItems:(NSArray *)items applicationActivities:(NSArray *)a;
@property (copy) void (^completionWithItemsHandler)(NSString *t, BOOL completed, NSArray *items, NSError *e);
@end
@interface UIStoryboard : NSObject
+ (instancetype)storyboardWithName:(NSString *)n bundle:(NSBundle *)b;
- (id)instantiateInitialViewController;
@end

/* ── WebKit ─────────────────────────────────────────────────────────── */
@protocol WKNavigationDelegate <NSObject> @end
@protocol WKUIDelegate <NSObject> @end
@protocol WKDownloadDelegate <NSObject> @end
@interface WKNavigation : NSObject @end
@interface WKFrameInfo : NSObject @end
@interface WKDownload : NSObject
@property (weak) id<WKDownloadDelegate> delegate;
@end
@interface WKNavigationAction : NSObject
@property (readonly) NSURLRequest *request;
@property (readonly) NSInteger navigationType;
@end
@interface WKNavigationResponse : NSObject
@property (readonly) BOOL canShowMIMEType;
@property (readonly) NSURLResponse *response;
@end
@interface WKWindowFeatures : NSObject @end
@interface WKWebsiteDataStore : NSObject
+ (instancetype)nonPersistentDataStore;
+ (instancetype)defaultDataStore;
@end
@interface WKWebpagePreferences : NSObject
- (void)setAllowsContentJavaScript:(BOOL)v;
@end
@interface WKWebViewConfiguration : NSObject
@property BOOL allowsInlineMediaPlayback;
@property (strong) WKWebsiteDataStore *websiteDataStore;
@property (copy) NSString *applicationNameForUserAgent;
@property (strong) WKWebpagePreferences *defaultWebpagePreferences;
@end
@interface WKWebView : UIView
- (instancetype)initWithFrame:(CGRect)f configuration:(WKWebViewConfiguration *)c;
@property (weak) id<WKNavigationDelegate> navigationDelegate;
@property (weak) id<WKUIDelegate> UIDelegate;
@property BOOL allowsBackForwardNavigationGestures;
- (void)evaluateJavaScript:(NSString *)js completionHandler:(void (^)(id, NSError *))c;
- (void)stopLoading;
- (void)goBack;
- (void)goForward;
@property (readonly) BOOL canGoBack;
@property (readonly) BOOL canGoForward;
@property (readonly) double estimatedProgress;
@property (readonly) BOOL isLoading;
- (void)loadRequest:(NSURLRequest *)r;
- (void)reload;
@property (readonly) UIScrollView *scrollView;
@property (copy) NSURL *URL;
@end

/* ── globals a source may reference ─────────────────────────────────── */
extern NSString *const NSURLErrorDomain;
extern const NSInteger NSURLErrorCancelled;
extern const NSUInteger NSUserDomainMask;
extern const NSUInteger NSDocumentDirectory;
extern const NSUInteger NSApplicationSupportDirectory;
extern const NSUInteger NSCachesDirectory;
#endif
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sources", nargs="*",
        default=["app/DSHRootViewController.m"],
        help="Objective-C sources to check (default: the app sources this repo changes)",
    )
    parser.add_argument("--tree", default="/tmp/objc-stub")
    args = parser.parse_args()

    out = args.tree
    os.makedirs(out, exist_ok=True)
    for header in HEADERS:
        path = os.path.join(out, header)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("#include \"DSHStubSDK.h\"\n" if header != "objc/runtime.h" else "")
    with open(os.path.join(out, "DSHStubSDK.h"), "w") as f:
        f.write(STUB)

    failures = 0
    for source in args.sources:
        cmd = [
            "clang", "-fsyntax-only", "-x", "objective-c",
            "-fobjc-arc", "-fobjc-runtime=macosx-10.15", "-fblocks",
            "-Wno-everything", "-Werror=objc-method-access",
            "-Werror=objc-property-implicit-mismatch",
            "-Werror=objc-interface-ivars",
            "-I", out, "-I", "app", "-I", "ish-arm64", "-I", "ish-arm64/app", source,
        ]
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        label = os.path.basename(source)
        if result.returncode == 0:
            print(f"ok   {label}")
        else:
            failures += 1
            print(f"FAIL {label}")
            print(result.stderr[:4000])
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
