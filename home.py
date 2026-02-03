from win32more.Microsoft.UI.Xaml import FrameworkElement
from win32more.Microsoft.UI.Xaml.Controls import Page, StackPanel, TextBlock, Button, Grid, NavigationView, NavigationViewItem
from win32more.Microsoft.UI.Xaml.Markup import XamlReader
from win32more.Windows.UI.Xaml.Interop import TypeKind
from win32more.Microsoft.UI.Xaml import Thickness, HorizontalAlignment, VerticalAlignment, CornerRadius
from win32more.Microsoft.UI.Xaml.Media import SolidColorBrush
from win32more.Windows.UI import Colors
from win32more.winui3 import xaml_typename
from modules.api import Api
from modules.config import Config
from chat import ChatPage
config = Config()

class HomePage(Page):  
    def __init__(self, app):  
        super().__init__()  
        self.app = app  

        from pathlib import Path

        xaml = f"""
<NavigationView xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\"
                xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\"
                x:Name=\"NavView\"
                IsBackButtonVisible=\"Collapsed\"
                IsSettingsVisible=\"False\"
                PaneDisplayMode=\"LeftCompact\"
                CompactPaneLength=\"50\">

    <NavigationView.PaneHeader>
        <Grid Height=\"72\" Width=\"72\">
            <Button x:Name=\"AvatarButton\" Width=\"48\" Height=\"48\" CornerRadius=\"0\"
                    Padding=\"0\" BorderThickness=\"0\"
                    HorizontalAlignment=\"Center\" VerticalAlignment=\"Center\" />
        </Grid>
    </NavigationView.PaneHeader>

    <NavigationView.MenuItems>
        <NavigationViewItem x:Name=\"ChatItem\" Tag=\"chat\" Content=\"Chat\">
            <NavigationViewItem.Icon>
                <FontIcon FontFamily=\"Segoe MDL2 Assets\" Glyph=\"&#xE715;\" />
            </NavigationViewItem.Icon>
        </NavigationViewItem>
        <NavigationViewItem x:Name=\"ContactsItem\" Tag=\"contacts\" Content=\"通讯录\">
            <NavigationViewItem.Icon>
                <FontIcon FontFamily=\"Segoe MDL2 Assets\" Glyph=\"&#xE77B;\" />
            </NavigationViewItem.Icon>
        </NavigationViewItem>
        <NavigationViewItem x:Name=\"CommunityItem\" Tag=\"community\" Content=\"社区\">
            <NavigationViewItem.Icon>
                <FontIcon FontFamily=\"Segoe MDL2 Assets\" Glyph=\"&#xE909;\" />
            </NavigationViewItem.Icon>
        </NavigationViewItem>
        <NavigationViewItem x:Name=\"DiscoverItem\" Tag=\"discover\" Content=\"发现\">
            <NavigationViewItem.Icon>
                <FontIcon FontFamily=\"Segoe MDL2 Assets\" Glyph=\"&#xE721;\" />
            </NavigationViewItem.Icon>
        </NavigationViewItem>
    </NavigationView.MenuItems>

    <Grid x:Name="ContentHost" Margin="0" />

</NavigationView>
"""

        root = XamlReader.Load(xaml).as_(NavigationView)
        fe = root.as_(FrameworkElement)
        self._content_host = fe.FindName("ContentHost").as_(Grid)

        avatar_button = fe.FindName("AvatarButton").as_(Button)
        chat_item = fe.FindName("ChatItem").as_(NavigationViewItem)
        contacts_item = fe.FindName("ContactsItem").as_(NavigationViewItem)
        community_item = fe.FindName("CommunityItem").as_(NavigationViewItem)
        discover_item = fe.FindName("DiscoverItem").as_(NavigationViewItem)

        try:
            print("[HomePage] loading avatar...")
            avatar_url = Api.AvatarUrlFromConfig()
            print(f"[HomePage] avatar_url: {avatar_url}")
            avatar_path = Api.DownloadAvatarToCache(avatar_url)
            print(f"[HomePage] avatar_path: {avatar_path}")
            if avatar_path:
                file_uri = Path(avatar_path).absolute().as_uri()
                avatar_xaml = f"""
<Image xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\"
       xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\"
       Width=\"48\" Height=\"48\" Stretch=\"Uniform\">
    <Image.Source>
        <BitmapImage UriSource=\"{file_uri}\" />
    </Image.Source>
</Image>
"""

                avatar_button.Content = XamlReader.Load(avatar_xaml)

        except Exception:
            import traceback

            print("[HomePage] avatar load failed")
            traceback.print_exc()
            avatar_button.Background = SolidColorBrush.CreateInstanceWithColor(Colors.LightGray)

        def on_exit_login(params, params2):
            config.set("token", "")
            self.app.main_frame.Navigate(xaml_typename("App.LoginPage", TypeKind.Custom))

        def show_home():
            self._content_host.Children.Clear()

            panel = StackPanel()
            panel.Spacing = 20
            panel.HorizontalAlignment = HorizontalAlignment.Center
            panel.VerticalAlignment = VerticalAlignment.Center

            welcome = TextBlock()
            welcome.Text = "欢迎来到主页！"
            welcome.FontSize = 32
            welcome.HorizontalAlignment = HorizontalAlignment.Center

            user_info = TextBlock()
            user_info.Text = "您已成功登录"
            user_info.FontSize = 16
            user_info.HorizontalAlignment = HorizontalAlignment.Center

            logout_button = Button()
            logout_button.Content = "退出登录"
            logout_button.Width = 200
            logout_button.Height = 40
            logout_button.HorizontalAlignment = HorizontalAlignment.Center
            logout_button.add_Click(on_exit_login)

            panel.Children.Append(welcome)
            panel.Children.Append(user_info)
            panel.Children.Append(logout_button)
            self._content_host.Children.Append(panel)

        def show_profile():
            self._content_host.Children.Clear()

            panel = StackPanel()
            panel.Spacing = 16
            panel.HorizontalAlignment = HorizontalAlignment.Center
            panel.VerticalAlignment = VerticalAlignment.Center

            title = TextBlock()
            title.Text = "个人资料"
            title.FontSize = 28
            title.HorizontalAlignment = HorizontalAlignment.Center

            back = Button()
            back.Content = "返回主页"
            back.Width = 200
            back.Height = 40
            back.HorizontalAlignment = HorizontalAlignment.Center
            back.add_Click(lambda p, a: show_home())

            panel.Children.Append(title)
            panel.Children.Append(back)
            self._content_host.Children.Append(panel)

        def show_placeholder(text):
            self._content_host.Children.Clear()

            panel = StackPanel()
            panel.Spacing = 16
            panel.HorizontalAlignment = HorizontalAlignment.Center
            panel.VerticalAlignment = VerticalAlignment.Center

            title = TextBlock()
            title.Text = text
            title.FontSize = 28
            title.HorizontalAlignment = HorizontalAlignment.Center

            back = Button()
            back.Content = "返回主页"
            back.Width = 200
            back.Height = 40
            back.HorizontalAlignment = HorizontalAlignment.Center
            back.add_Click(lambda p, a: show_home())

            panel.Children.Append(title)
            panel.Children.Append(back)
            self._content_host.Children.Append(panel)

        def on_nav_selection_changed(nv, args):
            item = args.SelectedItem
            try:
                item = item.as_(NavigationViewItem)
                tag = item.Tag.as_(str)
            except Exception:
                return

            if tag == "chat":
                self._content_host.Children.Clear()
                self._content_host.Children.Append(ChatPage(self.app))
            elif tag == "contacts":
                show_placeholder("通讯录")
            elif tag == "community":
                show_placeholder("社区")
            elif tag == "discover":
                show_placeholder("发现")

        root.SelectionChanged += on_nav_selection_changed
        root.SelectedItem = chat_item

        show_home()
        self.Content = root