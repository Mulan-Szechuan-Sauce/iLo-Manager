from django.shortcuts import redirect, render
from django.views.generic import TemplateView, View
from hpilo import Ilo

class VirtualMediaView(View):
    def get(self, request, *args, **kwargs):
        """
        Redirection to the VM summary page on access to /virtualMedia
        """
        return redirect('virtualMediaSummary')

class VirtualMediaSummaryView(TemplateView):
    def get(self, request, *args, **kwargs):
        """
        Generates the virtual media summary page
        """
        if request.session.get('valid_credentials_stored'):
            ilo = Ilo(request.session["hostname"],
                      request.session["username"],
                      request.session["password"],
                      delayed=True)
            ilo.get_vm_status('CDROM')
            ilo.get_vm_status('FLOPPY')
            results = ilo.call_delayed()
            print(results)
            vm_context = { }

            vm_context['cdrom'] = { }
            vm_context['cdrom']['boot'] = results[0]['boot_option']
            vm_context['cdrom']['image_inserted'] = results[0]['image_inserted']
            vm_context['cdrom']['image_url'] = \
                    results[0]['image_url'] if results[0]['image_url'] != '' else 'Not Applicable'
            vm_context['cdrom']['applet'] = results[0]['vm_applet']
            vm_context['cdrom']['write_protect'] = results[0]['write_protect']

            vm_context['floppy'] = { }
            vm_context['floppy']['boot'] = results[1]['boot_option']
            vm_context['floppy']['image_inserted'] = results[1]['image_inserted']
            vm_context['floppy']['image_url'] = results[1]['image_url']
            vm_context['floppy']['applet'] = results[1]['vm_applet']
            vm_context['floppy']['write_protect'] = results[1]['write_protect']

            return render(request, 'ilo2/virtual_media/virtualMediaSummary.html', vm_context)
        return render(request, 'ilo2/virtual_media/virtualMediaSummary.html')
