"""
Services catalog handlers for Abel Promotion bot.
Handles browsing platforms, listing services, and viewing service details.
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from database.repositories import ServiceRepository
from keyboards.services import (
    get_platform_keyboard,
    get_services_list_keyboard,
    get_service_detail_keyboard
)
from utils.localization import t

router = Router(name="services_router")

@router.message(Command("services"))
@router.message(F.text.in_(["🛍️ Services", "🛍️ አገልግሎቶች"]))
async def show_services_platforms(message: types.Message, lang: str):
    """Display available social media platforms."""
    text = t("select_platform", lang=lang)
    kb = get_platform_keyboard(lang=lang)
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "svc_platforms")
async def callback_svc_platforms(callback: types.CallbackQuery, lang: str):
    """Show platforms list via callback button."""
    text = t("select_platform", lang=lang)
    kb = get_platform_keyboard(lang=lang)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("svc_plat:"))
async def callback_svc_platform_selected(callback: types.CallbackQuery, lang: str):
    """List services under the selected platform."""
    platform = callback.data.split(":")[1]
    services = await ServiceRepository.get_active_by_platform(platform)

    if not services:
        await callback.message.edit_text(
            t("no_services_found", lang=lang),
            reply_markup=get_platform_keyboard(lang=lang),
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    text = t("select_service", lang=lang, platform=platform)
    kb = get_services_list_keyboard(services, platform=platform, lang=lang)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("svc_view:"))
async def callback_svc_view(callback: types.CallbackQuery, lang: str):
    """View details of a specific service."""
    service_id = int(callback.data.split(":")[1])
    service = await ServiceRepository.get_service_by_id(service_id)

    if not service:
        await callback.answer("Service not found.", show_alert=True)
        return

    pricing_unit = f"per unit (min: {service.minimum_quantity})" if service.pricing_type == "per_unit" else ""
    text = t(
        "service_details",
        lang=lang,
        name=service.get_name(lang),
        platform=service.platform,
        description=service.get_description(lang),
        price=int(service.price) if service.price.is_integer() else service.price,
        pricing_unit=pricing_unit,
        duration=service.get_duration(lang)
    )
    kb = get_service_detail_keyboard(service.id, platform=service.platform, lang=lang)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()
