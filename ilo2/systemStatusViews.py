from copy import deepcopy
from datetime import datetime
from socket import gaierror
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, View
from hpilo import Ilo, IloCommunicationError, IloLoginFailed

class IndexView(TemplateView):
    template_name = 'ilo2/index.html'

class SystemStatusView(View):
    def get(self, request, *args, **kwargs):
        """
        Redirection to the status summary page after a login, or on access to /status
        """
        return redirect('systemStatusSummary')

    def post(self, request, *args, **kwargs):
        """
        Facilitates login to the ilo2 interface
        """
        if request.session.get('valid_credentials_stored'):
            request.session["hostname"] = None
            request.session["username"] = None
            request.session["password"] = None
            request.session["valid_credentials_stored"] = False
            messages.success(request, "Diconnected from the server")
        else:
            try:
                ilo = Ilo(request.POST.get('hostname'),
                          request.POST.get('username'),
                        request.POST.get('password'))
                ilo.get_fw_version()
            except (IloCommunicationError, IloLoginFailed) as exception:
                if 'UNSUPPORTED_PROTOCOL' in exception.args[0]:
                    messages.warning(request, ('The server cannot connect to the iLo2 server '
                                               'due to an unsupported encryption algorithm. '
                                                '(Unsupported Protocol)'))
                elif 'Connection refused' in exception.args[0]:
                    messages.warning(request, ('Could not connect to the iLo2 server '
                                               '(Connection Refused)'))
                elif 'Login credentials rejected' in exception.args[0]:
                    messages.warning(request, "The provided credentials are incorrect")
                else:
                    raise
                return redirect(request.POST.get('next', 'systemStatus'))
            except gaierror as exception:
                if 'Name or service not known' in exception.args[1]:
                    messages.warning(request, ('An invalid hostname was provided '
                                               '(Name or service not known)'))
                else:
                    raise
                return redirect(request.POST.get('next', 'systemStatus'))

            request.session["hostname"] = request.POST.get('hostname')
            request.session["username"] = request.POST.get('username')
            request.session["password"] = request.POST.get('password')
            request.session["valid_credentials_stored"] = True
            messages.success(request, "Connected to the iLo2 server")
        return redirect(request.POST.get('next', 'systemStatus'))

class SystemStatusSummaryView(TemplateView):
    def get(self, request, *args, **kwargs):
        """
        Generates the system status summary page
        """
        if request.session.get('valid_credentials_stored'):
            ilo = Ilo(request.session["hostname"],
                      request.session["username"],
                      request.session["password"],
                      delayed=True)
            ilo.get_server_name()
            ilo.get_host_data()
            ilo.get_host_power_status()
            ilo.get_uid_status()
            ilo.get_fw_version()
            ilo.get_server_event_log()
            ilo.get_ilo_event_log()
            results = ilo.call_delayed()
            ilo_info_context = { }
            for entry in results[1]:
                if entry['type'] == 0:
                    ilo_info_context['bios_version'] = '{}; {}'.format(entry['Family'],
                                                                       entry['Date'])
                elif entry['type'] == 1:
                    ilo_info_context['server_serial'] = entry['Serial Number']
                    ilo_info_context['server_name'] = '{}; {}'.format(results[0],
                                                                      entry['Product Name'])
                    ilo_info_context['cUUID'] = entry['cUUID']
            ilo_info_context['power_status'] = results[2]
            ilo_info_context['uid_status'] = results[3]
            ilo_info_context['firmware_version'] = '{}; {}'.format(results[4]['firmware_version'],
                                                                   results[4]['firmware_date'])
            ilo_info_context['license_type'] = results[4]['license_type']
            ilo_info_context['latest_iml'] = results[5][-1]['description']
            # 2nd last log since the last log entry was the test login during authentication.
            ilo_info_context['latest_ilo'] = results[6][-2]['description']
            return render(request, 'ilo2/system_status/systemStatus.html', ilo_info_context)
        return render(request, 'ilo2/system_status/systemStatus.html')

class SystemStatusHealthView(TemplateView):
    def get(self, request, *args, **kwargs):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        """
        Generates the system health page
        """
        if request.session.get('valid_credentials_stored'):
            ilo = Ilo(request.session["hostname"],
                      request.session["username"],
                      request.session["password"],
                      delayed=True)
            ilo.get_embedded_health()
            ilo.get_power_readings()
            ilo.get_host_pwr_micro_ver()
            ilo.get_host_data()
            results = ilo.call_delayed()
            ilo_info_context = { }

            # Health Summary
            ilo_info_context["fan_summary"] = \
                '{}; {}'.format(results[0]['health_at_a_glance']['fans']['status'],
                                results[0]['health_at_a_glance']['fans']['redundancy'])
            ilo_info_context["temp_summary"] = \
                results[0]['health_at_a_glance']['temperature']['status']
            ilo_info_context["vrm_summary"] = results[0]['health_at_a_glance']['vrm']['status']
            ilo_info_context["psu_summary"] = \
                '{}; {}'.format(results[0]['health_at_a_glance']['power_supplies']['status'],
                                results[0]['health_at_a_glance']['power_supplies']['redundancy'])
            ilo_info_context["drive_summary"] = results[0]['health_at_a_glance']['drive']['status']

            # Fan Details
            ilo_info_context['fan_details'] = []
            for fan in results[0]['fans'].values():
                fan_info = { }
                fan_info['label'] = fan['label']
                fan_info['zone'] = '{} Zone'.format(fan['zone'])
                fan_info['status'] = fan['status']
                # TODO: Ensure the formatting is correct for more then just percentage
                #       Or is percentage always the case for iLo2?
                fan_info['speed'] = '{}%'.format(fan['speed'][0])
                ilo_info_context['fan_details'].append(fan_info)

            # Tempreature Details
            ilo_info_context['temp_details'] = []
            for temp_sensor in results[0]['temperature'].values():
                # iLo2 normally shows us all potential sensors, even if there is no sensor.
                if temp_sensor['status'] == 'n/a':
                    continue
                temp_info = { }
                temp_info['threshold'] = '{}°{}; {}°{}'.format(temp_sensor['caution'][0],
                                                               temp_sensor['caution'][1][0],
                                                               temp_sensor['critical'][0],
                                                               temp_sensor['critical'][1][0])
                temp_info['current'] = '{}°{}'.format(temp_sensor['currentreading'][0],
                                                      temp_sensor['currentreading'][1][0])
                temp_info['label'] = temp_sensor['label']
                temp_info['location'] = '{} Zone'.format(temp_sensor['location'])
                temp_info['status'] = temp_sensor['status']
                ilo_info_context['temp_details'].append(temp_info)

            # Power Supply Details
            # TODO: Find redundant PSU configurations
            ilo_info_context['current_power'] = \
                                '{} {} at {}'.format(results[1]['present_power_reading'][0],
                                                     results[1]['present_power_reading'][1],
                                                     datetime.now().strftime(r'%H:%M:%S %d/%m/%y'))
            ilo_info_context['power_firmware'] = results[2]
            ilo_info_context['power_supply_details'] = []
            for power_supply in results[0]['power_supplies'].values():
                psu_info = { }
                psu_info['label'] = power_supply['label']
                psu_info['status'] = power_supply['status']
                ilo_info_context['power_supply_details'].append(psu_info)

            # Processor, Memory and Network Details
            # TODO: Find the cache for the processors
            ilo_info_context["processor_details"] = []
            ilo_info_context["memory_details"] = []
            ilo_info_context["network_details"] = []
            for host_data in results[3]:
                if host_data['type'] == 4:
                    processor_info = {}
                    processor_info['label'] = host_data['Label']
                    processor_info['execution_technology'] = host_data['Execution Technology']
                    processor_info['memory_technology'] = host_data['Memory Technology']
                    processor_info['speed'] = host_data['Speed']
                    ilo_info_context["processor_details"].append(processor_info)
                elif host_data['type'] == 17:
                    memory_info = {}
                    memory_info['label'] = host_data['Label']
                    memory_info['size'] = host_data['Size']
                    if host_data['Size'] != "not installed":
                        memory_info['speed'] = \
                                        '{} (Current: {})'.format(host_data['Speed'],
                                                                  host_data['Current Speed'])
                    ilo_info_context["memory_details"].append(memory_info)
                elif host_data['type'] == 209:
                    network_info = {}
                    is_name_row = True
                    for row in host_data['fields'][1:]:
                        if is_name_row:
                            network_info['label'] = 'Port {}'.format(str(row['value']))
                            is_name_row = False
                        else:
                            network_info['mac'] = row['value']
                            ilo_info_context["network_details"].append(deepcopy(network_info))
                            is_name_row = True

            # Storage Details
            # TODO: Find storage details
            ilo_info_context["storage_details"] = []

            return render(request, 'ilo2/system_status/systemHealth.html', ilo_info_context)
        return render(request, 'ilo2/system_status/systemHealth.html')

class SystemStatusIloLogView(TemplateView):
    def get(self, request, *args, **kwargs):
        """
        Generates the iLo2 log page
        """
        if request.session.get('valid_credentials_stored'):
            ilo = Ilo(request.session["hostname"],
                      request.session["username"],
                      request.session["password"],
                      delayed=True)
            ilo.get_ilo_event_log()
            results = ilo.call_delayed()
            # We want logs from newest to oldest
            results[0].reverse()
            log_context = { 'events': [] }
            for entry in results[0]:
                log_entry = {}
                log_entry['severity'] = entry['severity']
                log_entry['class'] = entry['class']
                log_entry['last_update'] = entry['last_update']
                log_entry['initial_update'] = entry['initial_update']
                log_entry['count'] = str(entry['count'])
                log_entry['description'] = entry['description']
                log_context['events'].append(log_entry)

            return render(request, 'ilo2/system_status/displayLogs.html', log_context)
        return render(request, 'ilo2/system_status/displayLogs.html')

class SystemStatusIMLLogView(TemplateView):
    def get(self, request, *args, **kwargs):
        """
        Generates the IML (System events) log page
        """
        if request.session.get('valid_credentials_stored'):
            ilo = Ilo(request.session["hostname"],
                      request.session["username"],
                      request.session["password"],
                      delayed=True)
            ilo.get_server_event_log()
            results = ilo.call_delayed()
            # We want logs from newest to oldest
            results[0].reverse()
            log_context = { 'events': [] }
            for entry in results[0]:
                log_entry = {}
                log_entry['severity'] = entry['severity']
                log_entry['class'] = entry['class']
                log_entry['last_update'] = entry['last_update']
                log_entry['initial_update'] = entry['initial_update']
                log_entry['count'] = str(entry['count'])
                log_entry['description'] = entry['description']
                log_context['events'].append(log_entry)

            return render(request, 'ilo2/system_status/displayLogs.html', log_context)
        return render(request, 'ilo2/system_status/displayLogs.html')
