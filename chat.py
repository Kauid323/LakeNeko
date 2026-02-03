from win32more.Microsoft.UI.Xaml import FrameworkElement, HorizontalAlignment, VerticalAlignment, Visibility, Thickness
from win32more.Microsoft.UI.Xaml.Controls import Page, Grid, StackPanel, TextBlock, TextBox, ListView, ListViewItem, Image, Border, Button, MenuFlyout, MenuFlyoutItem, ContentDialog, ContentDialogResult
from win32more.Microsoft.UI.Xaml.Markup import XamlReader
from win32more.Microsoft.UI.Xaml.Media import SolidColorBrush
from win32more.Windows.UI import Color, Colors
from win32more.Microsoft.UI.Dispatching import DispatcherQueue
from win32more.Windows.System import VirtualKey

from modules.api import Api
import threading
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

class ChatPage(Page):
    _avatar_executor = ThreadPoolExecutor(max_workers=8)

    def __init__(self, app=None):
        super().__init__()
        self.app = app
        self._dispatcher = DispatcherQueue.GetForCurrentThread()
        self._is_active = True

        self._item_xaml = """
<ListViewItem xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\"
              xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\">
    <Grid Padding=\"8,6\">
        <Grid.ColumnDefinitions>
            <ColumnDefinition Width=\"44\" />
            <ColumnDefinition Width=\"*\" />
            <ColumnDefinition Width=\"Auto\" />
        </Grid.ColumnDefinitions>

        <Border Width=\"36\" Height=\"36\" CornerRadius=\"18\" Background=\"#FFE5E7EB\" Grid.Column=\"0\" VerticalAlignment=\"Center\">
            <Image x:Name=\"AvatarImage\" Width=\"36\" Height=\"36\" Stretch=\"UniformToFill\" />
        </Border>

        <StackPanel Grid.Column=\"1\" Spacing=\"2\" VerticalAlignment=\"Center\" Margin=\"10,0,10,0\">
            <TextBlock x:Name=\"TitleText\" FontSize=\"14\" FontWeight=\"SemiBold\" />
            <TextBlock x:Name=\"SubtitleText\" FontSize=\"12\" Opacity=\"0.75\" TextTrimming=\"CharacterEllipsis\" MaxLines=\"1\" />
        </StackPanel>

        <TextBlock x:Name=\"TimeText\" Grid.Column=\"2\" FontSize=\"11\" Opacity=\"0.6\" VerticalAlignment=\"Top\" />
    </Grid>
</ListViewItem>
"""

        self._msg_item_xaml = """
<ListViewItem xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\"
              xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\"
              HorizontalContentAlignment=\"Stretch\">
    <Grid x:Name=\"MsgRoot\" Margin=\"0,4\">
        <Grid.ColumnDefinitions>
            <ColumnDefinition Width=\"Auto\" />
            <ColumnDefinition Width=\"*\" />
            <ColumnDefinition Width=\"Auto\" />
        </Grid.ColumnDefinitions>
        
        <Border x:Name=\"AvatarBorder\" Width=\"32\" Height=\"32\" CornerRadius=\"16\" Background=\"#FFE5E7EB\" VerticalAlignment=\"Top\" Margin=\"0,4,8,0\" Grid.Column=\"0\">
            <Image x:Name=\"MsgAvatarImage\" Width=\"32\" Height=\"32\" Stretch=\"UniformToFill\" />
        </Border>

        <StackPanel x:Name="ContentPanel" Grid.Column="1" Spacing="2">
            <StackPanel Orientation="Horizontal" Spacing="6" x:Name="HeaderPanel">
                <TextBlock x:Name="MsgSenderName" FontSize="11" Opacity="0.6" VerticalAlignment="Center" />
                <StackPanel x:Name="MsgTagsContainer" Orientation="Horizontal" Spacing="4" VerticalAlignment="Center" />
            </StackPanel>
            <Border x:Name="BubbleBorder" Background="#FFF3F4F6" CornerRadius="6" Padding="10,8" HorizontalAlignment="Left" MaxWidth="400">
                <TextBlock x:Name="MsgText" FontSize="14" TextWrapping="Wrap" IsTextSelectionEnabled="True" />
            </Border>
            <TextBlock x:Name=\"MsgTime\" FontSize=\"10\" Opacity=\"0.4\" />
        </StackPanel>
        
        <Border x:Name=\"RightAvatarBorder\" Width=\"32\" Height=\"32\" CornerRadius=\"16\" Background=\"#FFE5E7EB\" VerticalAlignment=\"Top\" Margin=\"8,4,0,0\" Grid.Column=\"2\" Visibility=\"Collapsed\">
            <Image x:Name=\"MsgRightAvatarImage\" Width=\"32\" Height=\"32\" Stretch=\"UniformToFill\" />
        </Border>
    </Grid>
</ListViewItem>
"""

        xaml = """
<Grid xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\"
      xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\">
    <Grid.ColumnDefinitions>
        <ColumnDefinition Width=\"2*\" />
        <ColumnDefinition Width=\"3*\" />
    </Grid.ColumnDefinitions>

    <Grid x:Name=\"LeftPane\" Grid.Column=\"0\" Padding=\"0,12,12,12\">
        <Grid.RowDefinitions>
            <RowDefinition Height=\"Auto\" />
            <RowDefinition Height=\"*\" />
        </Grid.RowDefinitions>
        <TextBox x:Name=\"SearchBox\" Grid.Row=\"0\" PlaceholderText=\"搜索\" Margin=\"12,0,12,10\" />
        <ListView x:Name=\"ConversationList\" Grid.Row=\"1\" Padding=\"0\" SelectionMode=\"Single\" />
    </Grid>

    <Grid x:Name=\"RightPane\" Grid.Column=\"1\" Padding=\"12,12,12,12\" Background=\"White\">
        <Grid.RowDefinitions>
            <RowDefinition Height=\"Auto\" />
            <RowDefinition Height=\"*\" />
            <RowDefinition Height=\"Auto\" />
        </Grid.RowDefinitions>
        
        <TextBlock x:Name=\"ChatTitle\" Grid.Row=\"0\" Text=\"请选择一个会话\" FontSize=\"18\" FontWeight=\"Bold\" Margin=\"0,0,0,12\" />
        
        <ListView x:Name="MessageList" Grid.Row="1" Padding="0" SelectionMode="None">
            <ListView.Header>
                <Border x:Name="SentinelHeader" Height="1" Margin="0,0,0,0" Background="Transparent" />
            </ListView.Header>
            <ListView.ItemContainerStyle>
                <Style TargetType=\"ListViewItem\">
                    <Setter Property=\"MinHeight\" Value=\"0\" />
                    <Setter Property=\"Padding\" Value=\"0\" />
                </Style>
            </ListView.ItemContainerStyle>
        </ListView>

        <Grid x:Name=\"InputArea\" Grid.Row=\"2\" Margin=\"0,12,0,0\">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width=\"*\" />
                <ColumnDefinition Width=\"Auto\" />
            </Grid.ColumnDefinitions>
            <TextBox x:Name=\"MsgInput\" PlaceholderText=\"输入消息...\" AcceptsReturn=\"True\" MaxHeight=\"80\" />
            <Button x:Name=\"SendBtn\" Grid.Column=\"1\" Content=\"发送\" Margin=\"8,0,0,0\" VerticalAlignment=\"Bottom\" />
        </Grid>
    </Grid>
</Grid>
"""

        root = XamlReader.Load(xaml).as_(Grid)
        fe = root.as_(FrameworkElement)

        self._search_box = fe.FindName("SearchBox").as_(TextBox)
        self._list_view = fe.FindName("ConversationList").as_(ListView)
        self._title = fe.FindName("ChatTitle").as_(TextBlock)
        self._msg_list = fe.FindName("MessageList").as_(ListView)
        self._msg_input = fe.FindName("MsgInput").as_(TextBox)
        self._send_btn = fe.FindName("SendBtn").as_(Button)
        self._sentinel = fe.FindName("SentinelHeader").as_(Border)

        self._conversations = []
        self._current_chat = None
        self._conv_lookup = {} # chat_id -> data
        self._oldest_msg_id = None
        self._last_paging_msg_id = None # Track last used paging ID to avoid repeats
        self._is_loading_more = False
        self._active_load_token = 0
        self._msg_top_watch_handler = None
        self._msg_ccc_handler = None
        self._is_user_interacting = False
        self._last_interaction_time = 0
        import time

        def on_send_click(sender, args):
            if not self._current_chat or not self._msg_input.Text:
                return
            
            chat_id = self._current_chat.get("chatId") or self._current_chat.get("chat_id")
            chat_type = self._current_chat.get("chatType") or self._current_chat.get("chat_type")
            text = self._msg_input.Text
            
            def bg_send():
                try:
                    Api.SendMessageFromConfig(chat_id, int(chat_type), text)
                    def clear_ui():
                        self._msg_input.Text = ""
                        self._load_messages(self._current_chat)
                    self._dispatcher.TryEnqueue(clear_ui)
                except Exception as e:
                    print(f"[ChatPage] send failed: {e}")
            
            threading.Thread(target=bg_send, daemon=True).start()

        self._send_btn.add_Click(on_send_click)

        def on_selection_changed(sender, args):
            print(f"[ChatPage] SelectionChanged: AddedItems.Size={args.AddedItems.Size}")
            try:
                if args.AddedItems.Size == 0:
                    return
                
                selected_obj = args.AddedItems.GetAt(0)
                lvi = selected_obj.as_(ListViewItem)
                
                chat_id = lvi.Tag.as_(str) if hasattr(lvi.Tag, "as_") else str(lvi.Tag)
                print(f"[ChatPage] Selected chat_id: {chat_id}")
                
                conv_data = self._conv_lookup.get(chat_id)
                if not conv_data:
                    print(f"[ChatPage] No data found for chat_id: {chat_id}")
                    return

                # UI: switch conversation immediately, then load messages in background.
                self._current_chat = conv_data
                self._title.Text = conv_data.get("name") or "未知"

                # Reset pagination state for the new chat
                self._oldest_msg_id = None
                self._last_paging_msg_id = None
                self._is_loading_more = False

                # Bump token to invalidate in-flight loads from previous chat
                self._active_load_token += 1
                token = self._active_load_token

                self._msg_list.Items.Clear()
                try:
                    placeholder = XamlReader.Load('<ListViewItem xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"><TextBlock Text="加载中..." Opacity="0.6" Margin="0,8" /></ListViewItem>').as_(ListViewItem)
                    self._msg_list.Items.Append(placeholder)
                except:
                    pass

                self._load_messages(conv_data, load_token=token)
            except Exception as e:
                print(f"[ChatPage] selection changed error: {e}")

        self._list_view.SelectionChanged += on_selection_changed

        # Set up scroll listener for pagination
        def on_msg_list_loaded(sender, args):
            try:
                print("[ChatPage] MessageList Loaded: initializing sentinel hook")
                
                self._viewport_log_last = 0

                def on_sentinel_viewport_changed(s, e):
                    if not self._is_active or self._is_loading_more:
                        return
                    
                    try:
                        # Only trigger if sentinel is visible (EffectiveViewport.Height > 0)
                        if e.EffectiveViewport.Height > 0:
                            if self._oldest_msg_id and self._oldest_msg_id != self._last_paging_msg_id:
                                now = time.time()
                                # Strict check for user interaction to avoid infinite loops from auto-scrolling
                                # Increased tolerance for recent interaction to 2.0s to cover wheel inertia
                                recent_interaction = (now - self._last_interaction_time < 1.0)
                                if self._is_user_interacting or recent_interaction:
                                    print(f"[ChatPage] Sentinel visible (interacting). Triggering paging. Oldest: {self._oldest_msg_id}")
                                    self._load_messages(self._current_chat, is_load_more=True, load_token=self._active_load_token)
                                else:
                                    # Log but don't trigger if it seems like an auto-scroll
                                    if now - self._viewport_log_last > 2.0:
                                        print("[ChatPage] Sentinel visible but no recent user interaction. Skipping paging.")
                                        self._viewport_log_last = now
                    except Exception as ex:
                        print(f"[ChatPage] Sentinel error: {ex}")

                self._sentinel.EffectiveViewportChanged += on_sentinel_viewport_changed

            except Exception as e:
                print(f"[ChatPage] Scroll initialization error: {e}")

        self._msg_list.Loaded += on_msg_list_loaded

        # Track user interaction to prevent "auto-loading" loops
        self._wheel_timer = None
        
        def on_window_pasting(sender, args):
            try:
                from PIL import ImageGrab
                import io
                
                img = ImageGrab.grabclipboard()
                if img:
                    from PIL import Image
                    img_bytes = None
                    if isinstance(img, Image.Image):
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        img_bytes = buf.getvalue()
                    elif isinstance(img, list) and len(img) > 0:
                        file_path = img[0]
                        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                            with open(file_path, "rb") as f:
                                img_bytes = f.read()
                    
                    if img_bytes:
                        def show_confirm():
                            try:
                                dialog = ContentDialog()
                                dialog.Title = "发送图片"
                                dialog.Content = "检测到剪贴板中有图片，是否发送？"
                                dialog.PrimaryButtonText = "发送"
                                dialog.CloseButtonText = "取消"
                                dialog.XamlRoot = root.XamlRoot
                                
                                op = dialog.ShowAsync()
                                def on_dialog_completed(async_op, async_status):
                                    try:
                                        from win32more.Windows.Foundation import AsyncStatus
                                        if async_status == AsyncStatus.Completed:
                                            res = async_op.GetResults()
                                            if res == ContentDialogResult.Primary:
                                                self._upload_and_send_image(img_bytes)
                                    except Exception as ce:
                                        print(f"[ChatPage] Dialog completed error: {ce}")
                                
                                op.Completed = on_dialog_completed
                            except Exception as de:
                                print(f"[ChatPage] Dialog error: {de}")
                        
                        self._dispatcher.TryEnqueue(show_confirm)
                        if hasattr(args, "Handled"):
                            args.Handled = True
            except Exception as pe:
                print(f"[ChatPage] Paste handler error: {pe}")

        def on_input_paste(sender, args):
            on_window_pasting(sender, args)
        
        if hasattr(self._msg_input, "add_Paste"):
            self._msg_input.add_Paste(on_input_paste)

        def on_root_keydown(sender, args):
            if args.Key == VirtualKey.V:
                import ctypes
                is_ctrl_down = ctypes.windll.user32.GetKeyState(0x11) & 0x8000
                if is_ctrl_down:
                    on_window_pasting(sender, args)

        root.add_KeyDown(on_root_keydown)

        def on_pointer_pressed(s, e):
            self._is_user_interacting = True
            self._last_interaction_time = time.time()
        def on_pointer_released(s, e):
            self._is_user_interacting = False
            self._last_interaction_time = time.time()
        def on_pointer_exited(s, e):
            self._is_user_interacting = False
        def on_wheel(s, e):
            self._last_interaction_time = time.time()
            self._is_user_interacting = True
            # Reset the interacting flag after a short delay since wheel events are discrete
            if self._wheel_timer:
                self._wheel_timer.cancel()
            import threading
            def reset_interacting():
                self._is_user_interacting = False
            self._wheel_timer = threading.Timer(1.0, reset_interacting)
            self._wheel_timer.start()
            
        self._msg_list.PointerPressed += on_pointer_pressed
        self._msg_list.PointerReleased += on_pointer_released
        self._msg_list.PointerExited += on_pointer_exited
        self._msg_list.PointerWheelChanged += on_wheel

        def on_msg_input_keydown(sender, args):
            if args.Key == VirtualKey.Enter:
                on_send_click(None, None)

        self._msg_input.KeyDown += on_msg_input_keydown

        def _on_unloaded(sender, args):
            self._is_active = False
            print("[ChatPage] unloaded")

        self.Unloaded += _on_unloaded

        def on_text_changed(sender, args):
            try:
                self._apply_filter((self._search_box.Text or ""))
            except Exception:
                import traceback
                print("[ChatPage] search TextChanged handler failed")
                traceback.print_exc()

        self._search_box.TextChanged += on_text_changed

        self.Content = root
        self._load_conversations()

    def _upload_and_send_image(self, img_bytes):
        if not self._current_chat:
            return
            
        chat_id = self._current_chat.get("chatId") or self._current_chat.get("chat_id")
        chat_type = self._current_chat.get("chatType") or self._current_chat.get("chat_type")
        
        def bg_task():
            try:
                print(f"[ChatPage] Uploading image ({len(img_bytes)} bytes)...")
                # Upload to Qiniu via our new Api method
                img_meta = Api.UploadImage(None, img_bytes, "pasted_image.png")
                
                print(f"[ChatPage] Upload success, sending msg...")
                # Send the Protobuf message
                Api.SendImageMessageFromConfig(chat_id, int(chat_type), img_meta)
                
                def on_done():
                    self._load_messages(self._current_chat)
                self._dispatcher.TryEnqueue(on_done)
            except Exception as e:
                print(f"[ChatPage] Image upload/send failed: {e}")
                
        threading.Thread(target=bg_task, daemon=True).start()

    def _load_messages(self, conv_data, is_load_more=False, load_token=None):
        chat_id = conv_data.get("chatId") or conv_data.get("chat_id")
        chat_type = conv_data.get("chatType") or conv_data.get("chat_type")
        
        if not chat_id:
            return

        if self._is_loading_more:
            return
        
        # Use oldest msg_id for pagination if loading more
        msg_id = self._oldest_msg_id if is_load_more else ""

        # Avoid redundant requests for the same ID
        if is_load_more:
            if not msg_id:
                return
            if msg_id == self._last_paging_msg_id:
                return
            self._last_paging_msg_id = msg_id

        self._is_loading_more = True

        if load_token is None:
            load_token = self._active_load_token

        def bg_task():
            try:
                print(f"[ChatPage] Fetching: load_more={is_load_more}, msg_id='{msg_id}'")
                data = Api.MessageListFromConfig(chat_id=chat_id, chat_type=int(chat_type), msg_id=msg_id)
                msgs = data.get("msg") or []
                
                def update_ui():
                    try:
                        if not self._is_active:
                            return
                        if load_token != self._active_load_token:
                            return
                        if (self._current_chat and (self._current_chat.get("chatId") or self._current_chat.get("chat_id")) != chat_id):
                            return
                        
                        if not msgs:
                            print("[ChatPage] No more messages found")
                            return

                        # The last one in the list is the oldest from this batch
                        self._oldest_msg_id = msgs[-1].get("msgId") or msgs[-1].get("msg_id")
                        print(f"[ChatPage] Received {len(msgs)} msgs, new oldest_id='{self._oldest_msg_id}'")
                        
                        display_msgs = list(reversed(msgs))
                        
                        if not is_load_more:
                            self._msg_list.Items.Clear()
                            for m in display_msgs:
                                self._render_single_msg(m)
                            
                            # Scroll to bottom on initial load
                            count = self._msg_list.Items.Size
                            if count > 0:
                                last_item = self._msg_list.Items.GetAt(count - 1)
                                self._msg_list.ScrollIntoView(last_item)
                        else:
                            # Prepending older messages
                            first_item_before = self._msg_list.Items.GetAt(0) if self._msg_list.Items.Size > 0 else None
                            
                            for m in reversed(display_msgs):
                                self._render_single_msg(m, prepend=True)
                            
                            if first_item_before:
                                self._msg_list.ScrollIntoView(first_item_before)
                    finally:
                        self._is_loading_more = False
                
                self._dispatcher.TryEnqueue(update_ui)
            except Exception as e:
                print(f"[ChatPage] msg load failed: {e}")
                def reset_loading():
                    self._is_loading_more = False
                self._dispatcher.TryEnqueue(reset_loading)

        threading.Thread(target=bg_task, daemon=True).start()

    def _render_single_msg(self, m, prepend=False):
        try:
            # Import necessary modules inside the function to ensure they are available
            import win32more.Microsoft.UI.Xaml.Media
            import win32more.Microsoft.UI.Xaml
            from win32more.Microsoft.UI.Xaml import Visibility, HorizontalAlignment, FlowDirection, CornerRadius, Thickness, VerticalAlignment, UIElement
            from win32more.Microsoft.UI.Xaml.Media import SolidColorBrush
            from win32more.Windows.UI import Color, Colors
            from win32more.Microsoft.UI.Xaml.Controls import MenuFlyout, MenuFlyoutItem, Border, TextBlock, StackPanel, Image
            import win32more.Windows.UI.Text
            
            content = m.get("content", {})
            content_type = m.get("contentType") or m.get("content_type") or 1
            text = content.get("text") or ""
            image_url = content.get("imageUrl") or content.get("image_url") or ""
            
            sender = m.get("sender", {})
            sender_name = sender.get("name") or "未知"
            avatar_url = sender.get("avatarUrl") or sender.get("avatar_url") or ""
            send_time = m.get("sendTime") or m.get("send_time")
            direction = m.get("direction") or "left"

            lvi = XamlReader.Load(self._msg_item_xaml).as_(ListViewItem)
            fe = lvi.as_(FrameworkElement)
            name_tb = fe.FindName("MsgSenderName").as_(TextBlock)
            text_tb = fe.FindName("MsgText").as_(TextBlock)
            time_tb = fe.FindName("MsgTime").as_(TextBlock)
            content_panel = fe.FindName("ContentPanel").as_(StackPanel)
            bubble_border = fe.FindName("BubbleBorder").as_(Border)
            left_avatar_border = fe.FindName("AvatarBorder").as_(Border)
            right_avatar_border = fe.FindName("RightAvatarBorder").as_(Border)
            header_panel = fe.FindName("HeaderPanel").as_(StackPanel)
            
            # Tag elements
            tags_container = fe.FindName("MsgTagsContainer").as_(StackPanel)

            name_tb.Text = sender_name
            text_tb.Text = text
            
            # Handle multiple tags
            tags_list = sender.get("tag")
            if tags_list and isinstance(tags_list, list):
                for tag_data in tags_list:
                    if not isinstance(tag_data, dict): continue
                    tag_text = tag_data.get("text")
                    tag_color_str = tag_data.get("color")
                    if not tag_text: continue
                    
                    try:
                        # Create tag UI elements dynamically
                        t_border = Border()
                        t_border.CornerRadius = CornerRadius(TopLeft=4, TopRight=4, BottomRight=4, BottomLeft=4)
                        t_border.Padding = Thickness(Left=4, Top=1, Right=4, Bottom=1)
                        t_border.VerticalAlignment = VerticalAlignment.Center
                        
                        t_text = TextBlock()
                        t_text.Text = tag_text
                        t_text.FontSize = 9
                        t_text.Foreground = SolidColorBrush.CreateInstanceWithColor(Colors.White)
                        t_text.FontWeight = win32more.Windows.UI.Text.FontWeights.SemiBold
                        
                        t_border.Child = t_text.as_(UIElement)
                        
                        # Set background color
                        if tag_color_str:
                            c_str = tag_color_str.lstrip('#')
                            try:
                                if len(c_str) == 8: # AARRGGBB
                                    a, r, g, b = int(c_str[0:2], 16), int(c_str[2:4], 16), int(c_str[4:6], 16), int(c_str[6:8], 16)
                                    t_border.Background = SolidColorBrush.CreateInstanceWithColor(Color(A=a, R=r, G=g, B=b))
                                elif len(c_str) == 6: # RRGGBB
                                    r, g, b = int(c_str[0:2], 16), int(c_str[2:4], 16), int(c_str[4:6], 16)
                                    t_border.Background = SolidColorBrush.CreateInstanceWithColor(Color(A=255, R=r, G=g, B=b))
                                else:
                                    t_border.Background = SolidColorBrush.CreateInstanceWithColor(Colors.Gray)
                            except:
                                t_border.Background = SolidColorBrush.CreateInstanceWithColor(Colors.Gray)
                        else:
                            t_border.Background = SolidColorBrush.CreateInstanceWithColor(Colors.Gray)
                            
                        tags_container.Children.Append(t_border.as_(UIElement))
                    except Exception as te:
                        print(f"[ChatPage] Error creating tag UI for {sender_name}: {te}")

            if int(content_type) == 2 and image_url:
                text_tb.Visibility = Visibility.Collapsed
                img_control = Image()
                img_control.MaxWidth = 300
                img_control.Stretch = win32more.Microsoft.UI.Xaml.Media.Stretch.Uniform
                bubble_border.Child = img_control.as_(FrameworkElement)
                
                def load_msg_image():
                    thumb_img = image_url + ("&" if "?" in image_url else "?") + "imageView2/2/w/400"
                    path = Api.GetCachedImage(thumb_img)
                    if path and self._is_active:
                        file_uri = Path(path).absolute().as_uri()
                        def set_msg_img():
                            if not self._is_active: return
                            try:
                                img_source_xaml = f"<BitmapImage xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" UriSource=\"{file_uri}\" />"
                                img_control.Source = XamlReader.Load(img_source_xaml).as_(Image).Source
                            except: pass
                        self._dispatcher.TryEnqueue(set_msg_img)
                self._avatar_executor.submit(load_msg_image)
            else:
                text_tb.Text = text

            if direction == "right":
                left_avatar_border.Visibility = Visibility.Collapsed
                right_avatar_border.Visibility = Visibility.Visible
                content_panel.HorizontalAlignment = HorizontalAlignment.Right
                header_panel.HorizontalAlignment = HorizontalAlignment.Right
                header_panel.FlowDirection = FlowDirection.RightToLeft
                
                bubble_border.HorizontalAlignment = HorizontalAlignment.Right
                name_tb.HorizontalAlignment = HorizontalAlignment.Right
                time_tb.HorizontalAlignment = HorizontalAlignment.Right
                bubble_border.Background = SolidColorBrush.CreateInstanceWithColor(Color(A=255, R=149, G=236, B=105))
                avatar_img = fe.FindName("MsgRightAvatarImage").as_(Image)
            else:
                left_avatar_border.Visibility = Visibility.Visible
                right_avatar_border.Visibility = Visibility.Collapsed
                content_panel.HorizontalAlignment = HorizontalAlignment.Left
                header_panel.HorizontalAlignment = HorizontalAlignment.Left
                header_panel.FlowDirection = FlowDirection.LeftToRight
                
                bubble_border.HorizontalAlignment = HorizontalAlignment.Left
                name_tb.HorizontalAlignment = HorizontalAlignment.Left
                time_tb.HorizontalAlignment = HorizontalAlignment.Left
                bubble_border.Background = SolidColorBrush.CreateInstanceWithColor(Colors.White)
                avatar_img = fe.FindName("MsgAvatarImage").as_(Image)

            # Setup context menu for copying text
            try:
                menu = MenuFlyout()
                copy_item = MenuFlyoutItem()
                copy_item.Text = "复制文本"
                
                def on_copy_click(sender_obj, args):
                    try:
                        from win32more.Windows.ApplicationModel.DataTransfer import Clipboard, DataPackage
                        dp = DataPackage()
                        dp.SetText(text)
                        Clipboard.SetContent(dp)
                    except Exception as ce:
                        print(f"[ChatPage] Clipboard error: {ce}")
                
                copy_item.add_Click(on_copy_click)
                menu.Items.Append(copy_item)
                bubble_border.ContextFlyout = menu
            except Exception as me:
                print(f"[ChatPage] Menu setup error: {me}")

            if send_time:
                dt = datetime.datetime.fromtimestamp(int(send_time) / 1000.0)
                time_tb.Text = dt.strftime("%H:%M")
            
            if prepend:
                self._msg_list.Items.InsertAt(0, lvi)
            else:
                self._msg_list.Items.Append(lvi)
            
            if avatar_url:
                thumb_url = avatar_url + ("&" if "?" in avatar_url else "?") + "imageView2/2/w/60/h/60"
                def load_avatar_task():
                    path = Api.GetCachedImage(thumb_url)
                    if path and self._is_active:
                        file_uri = Path(path).absolute().as_uri()
                        def set_img():
                            if not self._is_active: return
                            try:
                                img_xaml = f"<Image xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\"><Image.Source><BitmapImage UriSource=\"{file_uri}\" /></Image.Source></Image>"
                                avatar_img.Source = XamlReader.Load(img_xaml).as_(Image).Source
                            except: pass
                        self._dispatcher.TryEnqueue(set_img)
                self._avatar_executor.submit(load_avatar_task)
        except Exception as e:
            print(f"[ChatPage] render msg error: {e}")

    def _load_conversations(self):
        def bg_task():
            try:
                print("[ChatPage] loading conversations in bg...")
                data = Api.ConversationListFromConfig()
                items = data.get("data") or []
                def update_ui():
                    self._conversations = items
                    self._apply_filter("")
                self._dispatcher.TryEnqueue(update_ui)
                print("[ChatPage] bg load finished")
            except Exception as e:
                print(f"[ChatPage] bg conversation load failed: {e}")

        threading.Thread(target=bg_task, daemon=True).start()

    def _apply_filter(self, query: str):
        q = (query or "").strip().lower()
        try:
            self._list_view.Items.Clear()
            self._conv_lookup.clear()
        except Exception:
            pass

        for conv in (self._conversations or []):
            name = (conv.get("name") or "").strip()
            content = (conv.get("chatContent") or conv.get("chat_content") or "").strip()
            avatar_url = (conv.get("avatarUrl") or conv.get("avatar_url") or "").strip()
            chat_id = conv.get("chatId") or conv.get("chat_id")
            ts_ms = conv.get("timestampMs") or conv.get("timestamp_ms")
            ts_s = conv.get("timestamp")

            if q and q not in name.lower() and q not in content.lower():
                continue

            lvi = XamlReader.Load(self._item_xaml).as_(ListViewItem)
            lvi.Tag = chat_id
            self._conv_lookup[chat_id] = conv
            
            fe = lvi.as_(FrameworkElement)
            title_tb = fe.FindName("TitleText").as_(TextBlock)
            subtitle_tb = fe.FindName("SubtitleText").as_(TextBlock)
            time_tb = fe.FindName("TimeText").as_(TextBlock)
            avatar_img = fe.FindName("AvatarImage").as_(Image)

            title_tb.Text = name
            subtitle_tb.Text = content

            try:
                now = datetime.datetime.now()
                if ts_ms: dt = datetime.datetime.fromtimestamp(int(ts_ms) / 1000.0)
                elif ts_s: dt = datetime.datetime.fromtimestamp(int(ts_s))
                else: dt = None
                
                if dt:
                    if dt.date() == now.date(): time_tb.Text = dt.strftime("%H:%M")
                    elif dt.year == now.year: time_tb.Text = dt.strftime("%m-%d")
                    else: time_tb.Text = dt.strftime("%Y-%m-%d")
            except: pass

            self._list_view.Items.Append(lvi)

            if avatar_url:
                thumb = avatar_url + ("&" if "?" in avatar_url else "?") + "imageView2/2/w/80/h/80"
                def load_avatar_bg(url, target_img):
                    try:
                        local_path = Api.GetCachedImage(url)
                        if local_path and self._is_active:
                            file_uri = Path(local_path).absolute().as_uri()
                            def update_avatar_ui():
                                if not self._is_active: return
                                try:
                                    img_xaml = f"<Image xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" Width=\"36\" Height=\"36\" Stretch=\"UniformToFill\"><Image.Source><BitmapImage UriSource=\"{file_uri}\" /></Image.Source></Image>"
                                    target_img.Source = XamlReader.Load(img_xaml).as_(Image).Source
                                except: pass
                            self._dispatcher.TryEnqueue(update_avatar_ui)
                    except: pass
                self._avatar_executor.submit(load_avatar_bg, thumb, avatar_img)
