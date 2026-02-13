"""Menu bar status item + settings window with history and account panels."""

import Cocoa
import objc

from muttr import config, history, account


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _label(text, font_size=13, bold=False, color=None):
    """Create an NSTextField used as a static label."""
    tf = Cocoa.NSTextField.alloc().initWithFrame_(Cocoa.NSZeroRect)
    tf.setStringValue_(text)
    tf.setBezeled_(False)
    tf.setDrawsBackground_(False)
    tf.setEditable_(False)
    tf.setSelectable_(False)
    if bold:
        tf.setFont_(Cocoa.NSFont.boldSystemFontOfSize_(font_size))
    else:
        tf.setFont_(Cocoa.NSFont.systemFontOfSize_(font_size))
    if color:
        tf.setTextColor_(color)
    tf.sizeToFit()
    return tf


def _separator(width):
    box = Cocoa.NSBox.alloc().initWithFrame_(Cocoa.NSMakeRect(0, 0, width, 1))
    box.setBoxType_(Cocoa.NSBoxSeparator)
    return box


def _ts_to_str(ts):
    """Format a unix timestamp as a readable string."""
    import datetime
    dt = datetime.datetime.fromtimestamp(ts)
    return dt.strftime("%b %d, %Y  %I:%M %p")


# ---------------------------------------------------------------------------
# Settings Window Controller
# ---------------------------------------------------------------------------

WINDOW_WIDTH = 560
WINDOW_HEIGHT = 480
TAB_GENERAL = 0
TAB_HISTORY = 1
TAB_ACCOUNT = 2


class SettingsWindowController:
    """Manages a native NSWindow with tabbed settings panels."""

    def __init__(self):
        self._window = None
        self._tab_view = None
        self._history_table = None
        self._history_data = []
        self._search_field = None
        self._cleanup_slider = None
        self._cleanup_label = None
        self._engine_popup = None
        self._model_popup = None
        # Account fields
        self._email_field = None
        self._name_field = None
        self._sign_in_button = None
        self._account_status_label = None

    def show(self):
        """Show the settings window, creating it if needed."""
        if self._window is None:
            self._build_window()
        self._refresh_history()
        self._refresh_account_ui()
        self._window.makeKeyAndOrderFront_(None)
        Cocoa.NSApp.activateIgnoringOtherApps_(True)

    def _build_window(self):
        style = (
            Cocoa.NSWindowStyleMaskTitled
            | Cocoa.NSWindowStyleMaskClosable
            | Cocoa.NSWindowStyleMaskMiniaturizable
        )
        rect = Cocoa.NSMakeRect(200, 200, WINDOW_WIDTH, WINDOW_HEIGHT)
        self._window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, Cocoa.NSBackingStoreBuffered, False
        )
        self._window.setTitle_("MuttR Settings")
        self._window.center()
        self._window.setReleasedWhenClosed_(False)

        # Tab view fills the window
        tab_rect = Cocoa.NSMakeRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self._tab_view = Cocoa.NSTabView.alloc().initWithFrame_(tab_rect)
        self._tab_view.setAutoresizingMask_(
            Cocoa.NSViewWidthSizable | Cocoa.NSViewHeightSizable
        )

        # -- General tab --
        general_item = Cocoa.NSTabViewItem.alloc().initWithIdentifier_("general")
        general_item.setLabel_("General")
        general_item.setView_(self._build_general_tab())
        self._tab_view.addTabViewItem_(general_item)

        # -- History tab --
        history_item = Cocoa.NSTabViewItem.alloc().initWithIdentifier_("history")
        history_item.setLabel_("History")
        history_item.setView_(self._build_history_tab())
        self._tab_view.addTabViewItem_(history_item)

        # -- Account tab --
        account_item = Cocoa.NSTabViewItem.alloc().initWithIdentifier_("account")
        account_item.setLabel_("Account")
        account_item.setView_(self._build_account_tab())
        self._tab_view.addTabViewItem_(account_item)

        self._window.contentView().addSubview_(self._tab_view)

    # ------------------------------------------------------------------
    # General Tab
    # ------------------------------------------------------------------

    def _build_general_tab(self):
        view = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT - 60)
        )
        cfg = config.load()
        y = view.frame().size.height - 40
        left = 24
        content_width = WINDOW_WIDTH - 48

        # --- Cleanup level ---
        title = _label("Cleanup Aggressiveness", font_size=13, bold=True)
        title.setFrameOrigin_(Cocoa.NSMakePoint(left, y))
        view.addSubview_(title)
        y -= 6

        level_names = ["Light", "Moderate", "Aggressive"]
        self._cleanup_label = _label(
            level_names[cfg["cleanup_level"]],
            font_size=11,
            color=Cocoa.NSColor.secondaryLabelColor(),
        )
        self._cleanup_label.setFrameOrigin_(Cocoa.NSMakePoint(left + 200, y + 2))
        view.addSubview_(self._cleanup_label)
        y -= 28

        self._cleanup_slider = Cocoa.NSSlider.alloc().initWithFrame_(
            Cocoa.NSMakeRect(left, y, content_width, 24)
        )
        self._cleanup_slider.setMinValue_(0)
        self._cleanup_slider.setMaxValue_(2)
        self._cleanup_slider.setNumberOfTickMarks_(3)
        self._cleanup_slider.setAllowsTickMarkValuesOnly_(True)
        self._cleanup_slider.setIntValue_(cfg["cleanup_level"])
        self._cleanup_slider.setTarget_(self)
        self._cleanup_slider.setAction_(objc.selector(self._cleanup_slider_changed_, signature=b"v@:@"))
        view.addSubview_(self._cleanup_slider)
        y -= 16

        desc = _label(
            "Controls how aggressively filler words and false starts are removed.",
            font_size=11,
            color=Cocoa.NSColor.secondaryLabelColor(),
        )
        desc.setFrameOrigin_(Cocoa.NSMakePoint(left, y))
        view.addSubview_(desc)
        y -= 32

        view.addSubview_(_separator(content_width))
        y -= 16

        # --- Transcription Engine ---
        eng_title = _label("Transcription Engine", font_size=13, bold=True)
        eng_title.setFrameOrigin_(Cocoa.NSMakePoint(left, y))
        view.addSubview_(eng_title)
        y -= 30

        self._engine_popup = Cocoa.NSPopUpButton.alloc().initWithFrame_pullsDown_(
            Cocoa.NSMakeRect(left, y, 200, 25), False
        )
        self._engine_popup.addItemsWithTitles_(["Whisper (faster-whisper)", "Parakeet-MLX"])
        engine_idx = 0 if cfg.get("transcription_engine", "whisper") == "whisper" else 1
        self._engine_popup.selectItemAtIndex_(engine_idx)
        self._engine_popup.setTarget_(self)
        self._engine_popup.setAction_(objc.selector(self._engine_changed_, signature=b"v@:@"))
        view.addSubview_(self._engine_popup)
        y -= 32

        # --- Whisper Model ---
        model_title = _label("Whisper Model Size", font_size=13, bold=True)
        model_title.setFrameOrigin_(Cocoa.NSMakePoint(left, y))
        view.addSubview_(model_title)
        y -= 30

        self._model_popup = Cocoa.NSPopUpButton.alloc().initWithFrame_pullsDown_(
            Cocoa.NSMakeRect(left, y, 200, 25), False
        )
        self._model_popup.addItemsWithTitles_(["base.en", "small.en"])
        model_idx = 0 if cfg["model"] == "base.en" else 1
        self._model_popup.selectItemAtIndex_(model_idx)
        self._model_popup.setTarget_(self)
        self._model_popup.setAction_(objc.selector(self._model_changed_, signature=b"v@:@"))
        view.addSubview_(self._model_popup)
        y -= 20

        model_desc = _label(
            "base.en is faster; small.en is more accurate but uses more memory.",
            font_size=11,
            color=Cocoa.NSColor.secondaryLabelColor(),
        )
        model_desc.setFrameOrigin_(Cocoa.NSMakePoint(left, y))
        view.addSubview_(model_desc)
        y -= 32

        view.addSubview_(_separator(content_width))
        y -= 16

        # --- Paste delay ---
        delay_title = _label("Paste Delay", font_size=13, bold=True)
        delay_title.setFrameOrigin_(Cocoa.NSMakePoint(left, y))
        view.addSubview_(delay_title)
        y -= 30

        self._delay_field = Cocoa.NSTextField.alloc().initWithFrame_(
            Cocoa.NSMakeRect(left, y, 80, 22)
        )
        self._delay_field.setIntValue_(cfg["paste_delay_ms"])
        self._delay_field.setFont_(Cocoa.NSFont.systemFontOfSize_(13))
        view.addSubview_(self._delay_field)

        ms_label = _label("ms", font_size=11, color=Cocoa.NSColor.secondaryLabelColor())
        ms_label.setFrameOrigin_(Cocoa.NSMakePoint(left + 86, y + 2))
        view.addSubview_(ms_label)

        save_delay_btn = Cocoa.NSButton.alloc().initWithFrame_(
            Cocoa.NSMakeRect(left + 120, y, 60, 24)
        )
        save_delay_btn.setTitle_("Save")
        save_delay_btn.setBezelStyle_(Cocoa.NSBezelStyleRounded)
        save_delay_btn.setTarget_(self)
        save_delay_btn.setAction_(objc.selector(self._save_delay_, signature=b"v@:@"))
        view.addSubview_(save_delay_btn)

        return view

    # ------------------------------------------------------------------
    # History Tab
    # ------------------------------------------------------------------

    def _build_history_tab(self):
        view = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT - 60)
        )
        h = view.frame().size.height
        left = 16
        content_width = WINDOW_WIDTH - 32

        # Search bar at top
        self._search_field = Cocoa.NSSearchField.alloc().initWithFrame_(
            Cocoa.NSMakeRect(left, h - 40, content_width - 100, 28)
        )
        self._search_field.setPlaceholderString_("Search transcriptions...")
        self._search_field.setTarget_(self)
        self._search_field.setAction_(objc.selector(self._search_changed_, signature=b"v@:@"))
        view.addSubview_(self._search_field)

        clear_btn = Cocoa.NSButton.alloc().initWithFrame_(
            Cocoa.NSMakeRect(content_width - 80 + left, h - 40, 80, 28)
        )
        clear_btn.setTitle_("Clear All")
        clear_btn.setBezelStyle_(Cocoa.NSBezelStyleRounded)
        clear_btn.setTarget_(self)
        clear_btn.setAction_(objc.selector(self._clear_history_, signature=b"v@:@"))
        view.addSubview_(clear_btn)

        # Scroll view with table
        scroll_rect = Cocoa.NSMakeRect(left, 8, content_width, h - 56)
        scroll_view = Cocoa.NSScrollView.alloc().initWithFrame_(scroll_rect)
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setBorderType_(Cocoa.NSBezelBorder)
        scroll_view.setAutoresizingMask_(
            Cocoa.NSViewWidthSizable | Cocoa.NSViewHeightSizable
        )

        self._history_table = Cocoa.NSTableView.alloc().initWithFrame_(Cocoa.NSZeroRect)
        self._history_table.setUsesAlternatingRowBackgroundColors_(True)
        self._history_table.setGridStyleMask_(Cocoa.NSTableViewSolidHorizontalGridLineMask)
        self._history_table.setRowHeight_(48)

        # Columns
        time_col = Cocoa.NSTableColumn.alloc().initWithIdentifier_("time")
        time_col.setWidth_(140)
        time_col.headerCell().setStringValue_("Time")
        self._history_table.addTableColumn_(time_col)

        text_col = Cocoa.NSTableColumn.alloc().initWithIdentifier_("text")
        text_col.setWidth_(content_width - 220)
        text_col.headerCell().setStringValue_("Transcription")
        self._history_table.addTableColumn_(text_col)

        engine_col = Cocoa.NSTableColumn.alloc().initWithIdentifier_("engine")
        engine_col.setWidth_(70)
        engine_col.headerCell().setStringValue_("Engine")
        self._history_table.addTableColumn_(engine_col)

        self._history_table.setDataSource_(self)
        self._history_table.setDelegate_(self)

        scroll_view.setDocumentView_(self._history_table)
        view.addSubview_(scroll_view)

        return view

    # ------------------------------------------------------------------
    # Account Tab
    # ------------------------------------------------------------------

    def _build_account_tab(self):
        view = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT - 60)
        )
        h = view.frame().size.height
        left = 24
        y = h - 40

        acct_title = _label("Account", font_size=16, bold=True)
        acct_title.setFrameOrigin_(Cocoa.NSMakePoint(left, y))
        view.addSubview_(acct_title)
        y -= 8

        self._account_status_label = _label(
            "", font_size=12, color=Cocoa.NSColor.secondaryLabelColor()
        )
        self._account_status_label.setFrameOrigin_(Cocoa.NSMakePoint(left + 100, y + 2))
        self._account_status_label.setFrame_(Cocoa.NSMakeRect(left + 100, y + 2, 300, 18))
        view.addSubview_(self._account_status_label)
        y -= 32

        view.addSubview_(_separator(WINDOW_WIDTH - 48))
        y -= 20

        email_label = _label("Email", font_size=13)
        email_label.setFrameOrigin_(Cocoa.NSMakePoint(left, y))
        view.addSubview_(email_label)
        y -= 26

        self._email_field = Cocoa.NSTextField.alloc().initWithFrame_(
            Cocoa.NSMakeRect(left, y, 280, 24)
        )
        self._email_field.setPlaceholderString_("you@example.com")
        self._email_field.setFont_(Cocoa.NSFont.systemFontOfSize_(13))
        view.addSubview_(self._email_field)
        y -= 32

        name_label = _label("Display Name", font_size=13)
        name_label.setFrameOrigin_(Cocoa.NSMakePoint(left, y))
        view.addSubview_(name_label)
        y -= 26

        self._name_field = Cocoa.NSTextField.alloc().initWithFrame_(
            Cocoa.NSMakeRect(left, y, 280, 24)
        )
        self._name_field.setPlaceholderString_("Your Name")
        self._name_field.setFont_(Cocoa.NSFont.systemFontOfSize_(13))
        view.addSubview_(self._name_field)
        y -= 36

        self._sign_in_button = Cocoa.NSButton.alloc().initWithFrame_(
            Cocoa.NSMakeRect(left, y, 120, 32)
        )
        self._sign_in_button.setBezelStyle_(Cocoa.NSBezelStyleRounded)
        self._sign_in_button.setTarget_(self)
        self._sign_in_button.setAction_(objc.selector(self._toggle_sign_in_, signature=b"v@:@"))
        view.addSubview_(self._sign_in_button)

        y -= 50
        view.addSubview_(_separator(WINDOW_WIDTH - 48))
        y -= 20

        prefs_title = _label("Preferences", font_size=13, bold=True)
        prefs_title.setFrameOrigin_(Cocoa.NSMakePoint(left, y))
        view.addSubview_(prefs_title)
        y -= 28

        self._auto_copy_check = Cocoa.NSButton.alloc().initWithFrame_(
            Cocoa.NSMakeRect(left, y, 300, 20)
        )
        self._auto_copy_check.setButtonType_(Cocoa.NSButtonTypeSwitch)
        self._auto_copy_check.setTitle_("Auto-copy transcriptions to clipboard")
        self._auto_copy_check.setTarget_(self)
        self._auto_copy_check.setAction_(objc.selector(self._pref_changed_, signature=b"v@:@"))
        view.addSubview_(self._auto_copy_check)
        y -= 26

        self._sound_check = Cocoa.NSButton.alloc().initWithFrame_(
            Cocoa.NSMakeRect(left, y, 300, 20)
        )
        self._sound_check.setButtonType_(Cocoa.NSButtonTypeSwitch)
        self._sound_check.setTitle_("Sound feedback on transcription complete")
        self._sound_check.setTarget_(self)
        self._sound_check.setAction_(objc.selector(self._pref_changed_, signature=b"v@:@"))
        view.addSubview_(self._sound_check)
        y -= 26

        self._overlay_check = Cocoa.NSButton.alloc().initWithFrame_(
            Cocoa.NSMakeRect(left, y, 300, 20)
        )
        self._overlay_check.setButtonType_(Cocoa.NSButtonTypeSwitch)
        self._overlay_check.setTitle_("Show recording overlay")
        self._overlay_check.setTarget_(self)
        self._overlay_check.setAction_(objc.selector(self._pref_changed_, signature=b"v@:@"))
        view.addSubview_(self._overlay_check)

        return view

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    @objc.python_method
    def _cleanup_slider_changed_(self, sender):
        val = int(sender.intValue())
        config.set_value("cleanup_level", val)
        names = ["Light", "Moderate", "Aggressive"]
        self._cleanup_label.setStringValue_(names[val])
        self._cleanup_label.sizeToFit()

    @objc.python_method
    def _engine_changed_(self, sender):
        engines = ["whisper", "parakeet"]
        config.set_value("transcription_engine", engines[sender.indexOfSelectedItem()])

    @objc.python_method
    def _model_changed_(self, sender):
        models = ["base.en", "small.en"]
        config.set_value("model", models[sender.indexOfSelectedItem()])

    @objc.python_method
    def _save_delay_(self, sender):
        try:
            val = int(self._delay_field.intValue())
            val = max(10, min(500, val))
            config.set_value("paste_delay_ms", val)
            self._delay_field.setIntValue_(val)
        except (ValueError, TypeError):
            pass

    @objc.python_method
    def _search_changed_(self, sender):
        query = str(self._search_field.stringValue()).strip()
        if query:
            self._history_data = history.search(query)
        else:
            self._history_data = history.get_recent()
        self._history_table.reloadData()

    @objc.python_method
    def _clear_history_(self, sender):
        alert = Cocoa.NSAlert.alloc().init()
        alert.setMessageText_("Clear All History?")
        alert.setInformativeText_(
            "This will permanently delete all transcription history. This cannot be undone."
        )
        alert.addButtonWithTitle_("Clear All")
        alert.addButtonWithTitle_("Cancel")
        alert.setAlertStyle_(Cocoa.NSAlertStyleWarning)
        if alert.runModal() == Cocoa.NSAlertFirstButtonReturn:
            history.clear_all()
            self._refresh_history()

    @objc.python_method
    def _toggle_sign_in_(self, sender):
        acct = account.load_account()
        if acct["signed_in"]:
            account.sign_out()
        else:
            email = str(self._email_field.stringValue()).strip()
            name = str(self._name_field.stringValue()).strip()
            if not email:
                return
            account.sign_in(email, name)
        self._refresh_account_ui()

    @objc.python_method
    def _pref_changed_(self, sender):
        prefs = {
            "auto_copy": bool(self._auto_copy_check.state()),
            "sound_feedback": bool(self._sound_check.state()),
            "show_overlay": bool(self._overlay_check.state()),
        }
        account.update_preferences(prefs)

    # ------------------------------------------------------------------
    # Refresh helpers
    # ------------------------------------------------------------------

    def _refresh_history(self):
        self._history_data = history.get_recent()
        if self._history_table:
            self._history_table.reloadData()

    def _refresh_account_ui(self):
        acct = account.load_account()
        if acct["signed_in"]:
            self._account_status_label.setStringValue_(
                f"Signed in as {acct['display_name']}"
            )
            self._email_field.setStringValue_(acct["email"])
            self._email_field.setEditable_(False)
            self._name_field.setStringValue_(acct["display_name"])
            self._name_field.setEditable_(False)
            self._sign_in_button.setTitle_("Sign Out")
        else:
            self._account_status_label.setStringValue_("Not signed in")
            self._email_field.setStringValue_("")
            self._email_field.setEditable_(True)
            self._name_field.setStringValue_("")
            self._name_field.setEditable_(True)
            self._sign_in_button.setTitle_("Sign In")
        prefs = acct["preferences"]
        self._auto_copy_check.setState_(
            Cocoa.NSControlStateValueOn if prefs.get("auto_copy") else Cocoa.NSControlStateValueOff
        )
        self._sound_check.setState_(
            Cocoa.NSControlStateValueOn if prefs.get("sound_feedback") else Cocoa.NSControlStateValueOff
        )
        self._overlay_check.setState_(
            Cocoa.NSControlStateValueOn if prefs.get("show_overlay") else Cocoa.NSControlStateValueOff
        )

    # ------------------------------------------------------------------
    # NSTableViewDataSource
    # ------------------------------------------------------------------

    def numberOfRowsInTableView_(self, table_view):
        return len(self._history_data)

    def tableView_objectValueForTableColumn_row_(self, table_view, column, row):
        if row >= len(self._history_data):
            return ""
        entry = self._history_data[row]
        col_id = str(column.identifier())
        if col_id == "time":
            return _ts_to_str(entry["timestamp"])
        elif col_id == "text":
            text = entry["cleaned_text"] or entry["raw_text"]
            return text[:120] + ("..." if len(text) > 120 else "")
        elif col_id == "engine":
            return entry.get("engine", "whisper")
        return ""


# ---------------------------------------------------------------------------
# Menu Bar Status Item
# ---------------------------------------------------------------------------

class MenuBar:
    """NSStatusBar item with dropdown menu that opens the settings window."""

    def __init__(self):
        self._status_item = None
        self._settings_controller = SettingsWindowController()

    def setup(self):
        """Create the status bar item. Must be called on the main thread."""
        status_bar = Cocoa.NSStatusBar.systemStatusBar()
        self._status_item = status_bar.statusItemWithLength_(
            Cocoa.NSVariableStatusItemLength
        )
        button = self._status_item.button()
        button.setTitle_("M")
        button.setFont_(Cocoa.NSFont.boldSystemFontOfSize_(14))

        menu = Cocoa.NSMenu.alloc().init()

        settings_item = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Settings...", objc.selector(self._open_settings_, signature=b"v@:@"), ","
        )
        settings_item.setTarget_(self)
        menu.addItem_(settings_item)

        menu.addItem_(Cocoa.NSMenuItem.separatorItem())

        quit_item = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit MuttR", objc.selector(self._quit_, signature=b"v@:@"), "q"
        )
        quit_item.setTarget_(self)
        menu.addItem_(quit_item)

        self._status_item.setMenu_(menu)

    @objc.python_method
    def _open_settings_(self, sender):
        self._settings_controller.show()

    @objc.python_method
    def _quit_(self, sender):
        Cocoa.NSApp.terminate_(None)
