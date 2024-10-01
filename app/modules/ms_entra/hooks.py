import asyncio

from core.utils.logging import logger as log
from core.schemas import database

# AdminPanel UI
from core.modules.admin_panel import ui

from .schema import Tenant, MigrationJob
from .src import msapp


def edit_migration_details(item: dict, base_model: database.DatabaseMongoBaseModel ):
    if base_model.collection_name() == "ms_entra_migration_job":
        job = MigrationJob(**item)
        log.warning(f"Callback 'crud_item_created' executed: {item}")
        # print(type(job), job)
        # print(job.name)
        ui.navigate.to(f"/ms_entra/migrate-job/{job.id}")
        # with ui.dialog() as dialog, ui.card():
        #     ui.label(f"New Migration Job Created: {job.id}")
        # dialog.open()

def crud_interface_buttons(base_model: database.DatabaseMongoBaseModel, selected_items = None):
    if base_model.collection_name() == "ms_entra_tenants":
        
        async def _click_test():
            items = selected_items()
            
            if items and len(items)>0:
                                
                n = ui.notification(timeout=None, close_button=True)
                n.message = f'Testing Connections'
                await asyncio.sleep(0.2)
                n.spinner = True
                report = []
                for item in items:
                    n.message = f'Testing Connection to "{item["name"]}"'
                    await asyncio.sleep(0.3)
                    
                     # Prepare tenant object
                    try:
                        tenant = msapp.connect_tenant(item)
                        
                        if tenant and tenant.access_token:
                            n.message = f'✅ Connection Successful to "{item["name"]}"'
                            report.append(f"✅ {item['name']} ")
                        else:
                            raise Exception("Failed to connect to Tenant")
                        
                    except Exception as e:
                        log.error(e)
                        n.message = f'❌ Failed to connect to "{item["name"]}"'
                        report.append(f"❌ {item['name']} - {e}")
                        
                    await asyncio.sleep(0.3)
                    
                n.message = 'Done!'
                n.spinner = False
                
                with ui.dialog() as dialog, ui.card().classes('w-full full-width h-4/5'):
                    ui.label("Testing Connections")
                    ui.separator()
                    ui.label("This will test the connections to the selected tenants.")
                    ui.textarea(value='\n'.join(report)).classes('w-full full-width').style('height:100%;')
                    ui.separator()
                    ui.button("Close", on_click=dialog.close)

                n.dismiss()
                
                dialog.open()

            else:
                ui.notification("Select an item first.", position='center', type='negative', icon='error', timeout=1)
                
        ui.button("Test Connection", on_click=_click_test)
        
        
    if base_model.collection_name() == "ms_entra_migration_job":
        
        def _click_edit():
            if selected_items:
                # ui.notification("Click!", position='center', type='positive', icon='check', timeout=1)
                item = selected_items()
                if len(item) != 1:
                    ui.notification("Select a single item to modify.", position='center', type='negative', icon='error', timeout=1)
                    return
                job = MigrationJob(**item[0])   
                # ui.navigate.to(f"/ms_entra/migrate-job/{job.id}")
                ui.navigate.to(f"/ticket/view/{job.id}")
                
        def _click_exec():
            if selected_items:
                # ui.notification("Click!", position='center', type='positive', icon='check', timeout=1)
                item = selected_items()
                if len(item) != 1:
                    ui.notification("Select a single item to modify.", position='center', type='negative', icon='error', timeout=1)
                    return
                job = MigrationJob(**item[0])   
                if job.status != "APPROVED":
                    ui.notification("Job must be in 'APPROVED' status to execute.", position='center', type='negative', icon='error', timeout=1)
                    return
                
                ui.navigate.to(f"/ms_entra/migrate-job/{job.id}?tab=execute")

        # ui.button("Edit Job Details", on_click=_click_edit)
        # ui.button("Execute Job", on_click=_click_exec)
        ui.button("View Job", on_click=_click_edit)