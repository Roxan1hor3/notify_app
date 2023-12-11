from src.notify.taskapp.app import AppContext, async_run_task


@async_run_task
async def send_billing_messages_in_telegram(ctx: AppContext):
    await ctx.notify_service.send_billing_messages_in_telegram()
