from win32more.Microsoft.UI.Xaml import Thickness, HorizontalAlignment
from win32more.Microsoft.UI.Xaml.Controls import (  
    StackPanel, TextBox, PasswordBox, CheckBox, Button, TextBlock, Page
)  
from win32more.Microsoft.UI.Xaml.Media import SolidColorBrush  
from win32more.Windows.UI import Colors  
from modules.api import Api
from modules.config import Config
config = Config()
class LoginPage(Page):  
    def __init__(self, app):  
        super().__init__()  
        self.app = app  # 保存应用引用以便导航  
          
        panel = StackPanel()  
        panel.Margin = Thickness(40, 40, 40, 40)  
        panel.Spacing = 15  
          
        # 标题  
        title = TextBlock()  
        title.Text = "用户登录"  
        title.FontSize = 24  
        title.HorizontalAlignment = HorizontalAlignment.Left  
        title.Margin = Thickness(0, 0, 0, 5)  
          
        # 副标题  
        subtitle = TextBlock()  
        subtitle.Text = "请输入邮箱和密码"  
        subtitle.FontSize = 13  
        subtitle.HorizontalAlignment = HorizontalAlignment.Left  
        subtitle.Margin = Thickness(0, -17, 0, 40)  
        subtitle.Foreground = SolidColorBrush.CreateInstanceWithColor(Colors.Gray)  
          
        # 邮箱标签  
        email_label = TextBlock()  
        email_label.Text = "邮箱"  
        email_label.FontSize = 14  
        email_label.HorizontalAlignment = HorizontalAlignment.Center  
        email_label.Margin = Thickness(-300, 0, 0, -5)  
          
        # 邮箱输入框  
        self.email_box = TextBox()  
        self.email_box.PlaceholderText = "请输入邮箱"  
        self.email_box.Width = 300  
        self.email_box.HorizontalAlignment = HorizontalAlignment.Center  
          
        # 密码标签  
        password_label = TextBlock()  
        password_label.Text = "密码"  
        password_label.FontSize = 14  
        password_label.HorizontalAlignment = HorizontalAlignment.Center  
        password_label.Margin = Thickness(-300, 0, 0, -5)  
          
        # 密码输入框  
        self.password_box = PasswordBox()  
        self.password_box.PlaceholderText = "请输入密码"  
        self.password_box.Width = 300  
        self.password_box.HorizontalAlignment = HorizontalAlignment.Center  
          
        # 同意协议复选框  
        self.agree_checkbox = CheckBox()  
        self.agree_checkbox.Content = "我已阅读并同意用户协议"  
        self.agree_checkbox.HorizontalAlignment = HorizontalAlignment.Center  
          
        # 登录按钮  
        self.login_button = Button()  
        self.login_button.Content = "登录"  
        self.login_button.Width = 300  
        self.login_button.Height = 40  
        self.login_button.FontSize = 16  
        self.login_button.HorizontalAlignment = HorizontalAlignment.Center  
          
        purple_brush = SolidColorBrush()  
        purple_brush.Color = Colors.LightBlue  
        self.login_button.Background = purple_brush  
        self.login_button.add_Click(self.on_login_click)  
          
        # 手机号登录按钮  
        self.phone_button = Button()  
        self.phone_button.Content = "手机号登录"  
        self.phone_button.Width = 300  
        self.phone_button.Height = 40  
        self.phone_button.FontSize = 16  
        self.phone_button.HorizontalAlignment = HorizontalAlignment.Center  
        self.phone_button.Background = None  
          
        # 忘记密码按钮  
        self.forgot_password_button = Button()  
        self.forgot_password_button.Content = "忘记密码?点我找回!"  
        self.forgot_password_button.FontSize = 12  
        self.forgot_password_button.HorizontalAlignment = HorizontalAlignment.Right  
        self.forgot_password_button.Margin = Thickness(0, -10, 40, 0)  
        self.forgot_password_button.Background = None  
        self.forgot_password_button.BorderThickness = Thickness(0, 0, 0, 0)  
          
        # 状态消息  
        self.status_message = TextBlock()  
        self.status_message.Text = ""  
        self.status_message.FontSize = 13  
        self.status_message.HorizontalAlignment = HorizontalAlignment.Center  
        self.status_message.Margin = Thickness(0, -10, 0, 0)  
          
        # 添加所有控件  
        panel.Children.Append(title)  
        panel.Children.Append(subtitle)  
        panel.Children.Append(email_label)  
        panel.Children.Append(self.email_box)  
        panel.Children.Append(password_label)  
        panel.Children.Append(self.password_box)  
        panel.Children.Append(self.agree_checkbox)  
        panel.Children.Append(self.login_button)  
        panel.Children.Append(self.phone_button)  
        panel.Children.Append(self.forgot_password_button)  
        panel.Children.Append(self.status_message)  
          
        self.Content = panel  
      
    def on_login_click(self, sender, args):  
        email = self.email_box.Text  
        password = self.password_box.Password  
        is_agreed = self.agree_checkbox.IsChecked  
          
        self.status_message.Text = ""  
          
        if not email:  
            self.status_message.Text = "请输入邮箱"  
            self.status_message.Foreground = SolidColorBrush.CreateInstanceWithColor(Colors.Red)  
            return  
          
        if not password:  
            self.status_message.Text = "请输入密码"  
            self.status_message.Foreground = SolidColorBrush.CreateInstanceWithColor(Colors.Red)  
            return  
          
        if not is_agreed:  
            self.status_message.Text = "请同意用户协议"  
            self.status_message.Foreground = SolidColorBrush.CreateInstanceWithColor(Colors.Red)  
            return  
          
        self.status_message.Text = "登录中..."  
        self.status_message.Foreground = SolidColorBrush.CreateInstanceWithColor(Colors.Blue)  
          
        try:  
            response = Api.EmailLogin(email, password)  
              
            if response.status_code == 200:  
                result = response.json()  
                  
                if result.get("code") == 1:  
                    token = result["data"]["token"]  
                    config.set("token", token)  
                      
                    # 登录成功后导航到主页  
                    self.app.navigate_to_home()  
                else:  
                    error_msg = result.get("msg", "登录失败")  
                    self.status_message.Text = f"登录失败: {error_msg}"  
                    self.status_message.Foreground = SolidColorBrush.CreateInstanceWithColor(Colors.Red)  
            else:  
                self.status_message.Text = f"网络请求失败: {response.status_code}"  
                self.status_message.Foreground = SolidColorBrush.CreateInstanceWithColor(Colors.Red)  
        except Exception as e:  
            self.status_message.Text = f"登录异常: {str(e)}"  
            self.status_message.Foreground = SolidColorBrush.CreateInstanceWithColor(Colors.Red)