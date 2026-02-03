from win32more.Microsoft.UI.Xaml import Window, ApplicationTheme
from win32more.Microsoft.UI.Xaml.Controls import Frame
from win32more.Windows.Graphics import SizeInt32  
from win32more.Windows.UI.Xaml.Interop import TypeKind  
from win32more.winui3 import XamlApplication, XamlType, xaml_typename  
 
from modules.config import Config  
from login import LoginPage
from home import HomePage
config = Config()  
  
class LoginApp(XamlApplication):  
    def __init__(self):  
        super().__init__()  
        self.RequestedTheme = ApplicationTheme.Light  
      
    def OnLaunched(self, args):  
        self.window = Window()  
        self.window.Title = "LakeNeko"  
        self.window.AppWindow.Resize(SizeInt32(Width=500, Height=600))  
          
        # 创建 Frame 作为主容器  
        self.main_frame = Frame()  
        self.window.Content = self.main_frame  
        token = config.get("token")
        if not token:
            self.main_frame.Navigate(xaml_typename("App.LoginPage", TypeKind.Custom))  
        else:
            self.main_frame.Navigate(xaml_typename("App.HomePage", TypeKind.Custom))
          
        self.window.Activate()  
      
    def GetXamlTypeByFullName(self, typename):  
        if typename == "App.LoginPage":  
            return XamlType("App.LoginPage", TypeKind.Custom,   
                          activate_instance=lambda: LoginPage(self))  
        elif typename == "App.HomePage":  
            return XamlType("App.HomePage", TypeKind.Custom,  
                          activate_instance=lambda: HomePage(self))  
        return super().GetXamlTypeByFullName(typename)  
      
    def navigate_to_home(self):  
        """导航到主页"""  
        self.main_frame.Navigate(xaml_typename("App.HomePage", TypeKind.Custom))


XamlApplication.Start(LoginApp)