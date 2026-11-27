Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
exe = files.BuildPath(folder, "dist\Performance Air.exe")
If files.FileExists(exe) Then
    shell.Run """" & exe & """", 0, False
Else
    shell.Run "pythonw.exe """ & files.BuildPath(folder, "main.py") & """", 0, False
End If
