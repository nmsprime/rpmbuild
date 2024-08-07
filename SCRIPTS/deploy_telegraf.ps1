param (
    [ValidateScript({Test-Path $_ -PathType Leaf})]
    [string] $telegrafZipPath,
    [Parameter(Mandatory=$true)]
    [string] $syslogServerHostname,
    [string] $serviceUser,
    [string] $serviceUserPassword
)

# Define the content of the custom Telegraf configuration
$telegrafConfig = @"
[agent]
  interval = "20s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000
  collection_jitter = "0s"
  flush_interval = "20s"
  flush_jitter = "0s"

[[inputs.win_eventlog]]
  name_prefix = "Telegraf_"

  # xpath_query = "Event/*[System[EventID=4624 or EventID=4634 or EventID=4625]]"
  xpath_query = '''
    <QueryList>
      <Query Id="0" Path="Security">
        <Select Path="Security">
          *[System[EventID=4624 or EventID=4634]] and *[EventData[Data[@Name='LogonType']!="5"]]
        </Select>
      </Query>
      <Query Id="1" Path="Security">
        <Select Path="Security">
          *[System[EventID=4625 or EventID=4647]]
        </Select>
      </Query>
    </QueryList>
  '''

  event_tags = [
    "EventID",
    "TaskText",
    "OpcodeText",
    "Channel",
    "Computer",
    ]

  event_fields = [
    "Version",
    "Data_LogonType",
    "Data_TargetDomainName",
    "Data_TargetUserName",
    "Message",
    "TimeCreated",
    "Data_IpAddress",
    "Data_IpPort",
  ]

[[processors.rename]]
  [[processors.rename.replace]]
    tag="OpcodeText"
    dest="severity"

  [[processors.rename.replace]]
    tag="Computer"
    dest="facility"

  [[processors.rename.replace]]
    field="Version"
    dest="version"

  [[processors.rename.replace]]
    field="Message"
    dest="message"

[[outputs.syslog]]
  address = "udp://$syslogServerHostname`:514"
  sdids = [
    "Data_LogonType",
    "Data_TargetDomainName",
    "Data_TargetUserName",
    'Data_FailureReason',
    "Message",
    "TimeCreated",
    "Data_IpAddress",
    "Data_IpPort",
  ]
  default_appname = "Telegraf LoginLogs"
"@

# Define other variables
[string] $telegrafExtractPath = "$env:TEMP\telegraf"
[string] $telegrafInstallPath = "C:\Program Files\Telegraf"
[string] $telegrafConfigFile = "C:\Program Files\Telegraf\telegraf.conf"
[string] $serviceName = "Telegraf"

if ($telegrafZipPath) {
  $verifiedZipPath = $telegrafZipPath
}

if (-not ($verifiedZipPath)) {
    $telegrafDownloadUrl = "https://dl.influxdata.com/telegraf/releases/telegraf-1.29.2_windows_amd64.zip"
    $verifiedZipPath = "$env:TEMP\telegraf-1.29.2.zip"
    [bool] $download = $true

    Invoke-WebRequest -Uri $telegrafDownloadUrl -OutFile $verifiedZipPath
}

# Extract Telegraf archive
Expand-Archive -Path $verifiedZipPath -DestinationPath $telegrafExtractPath

# Create install directory if it doesn't exist
if (-not (Test-Path $telegrafInstallPath)) {
    New-Item -ItemType Directory -Path $telegrafInstallPath | Out-Null
}

$service = Get-WMIObject -class Win32_Service -filter "name='$serviceName'"

# Copy extracted files to the installation directory
if ($service) {
  Stop-Service -Name $serviceName
}

Copy-Item -Path "$telegrafExtractPath\telegraf-1.29.2\*" -Destination $telegrafInstallPath -Recurse

# Create the Telegraf Config
$telegrafConfig | Set-Content -Path $telegrafConfigFile -Force


if (-not ($service)) {
  # Install Telegraf as a service
  & "$telegrafInstallPath\telegraf.exe" --service install --config "$telegrafConfigFile" --service-name $serviceName --service-auto-restart

  # Set user and password to server to be available at boot and lock screens
  if ($serviceUser -And $serviceUserPassword) {
    $service.change($null, $null, $null, $null, $null, $false, ".\$serviceUser", "$serviceUserPassword")
  }
}

# Start the Telegraf service
Start-Service -Name $serviceName

# Clean up temporary files
Remove-Item $telegrafExtractPath -Recurse -Force

if ($download) {
    Remove-Item $verifiedZipPath -Force
}
