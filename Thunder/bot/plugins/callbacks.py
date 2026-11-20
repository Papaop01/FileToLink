# Thunder/bot/plugins/callbacks.py

import asyncio

from pyrogram import Client, enums, filters
from pyrogram.errors import FloodWait, MessageNotModified, MessageDeleteForbidden
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup)

from Thunder.bot import StreamBot
from Thunder.bot.plugins.stream import get_link_buttons
from Thunder.utils.bot_utils import gen_canonical_links
from Thunder.utils.broadcast import broadcast_ids
from Thunder.utils.canonical_files import (
    get_file_by_unique_id,
    is_link_active,
    regenerate_canonical_link,
    revoke_canonical_file,
)
from Thunder.utils.decorators import get_shortener_status, owner_only
from Thunder.utils.logger import logger
from Thunder.utils.messages import (
    MSG_ABOUT, MSG_BROADCAST_CANCEL, MSG_BUTTON_ABOUT, MSG_BUTTON_CLOSE,
    MSG_BUTTON_GET_HELP, MSG_BUTTON_GITHUB, MSG_BUTTON_JOIN_CHANNEL,
    MSG_BUTTON_REGENERATE_LINK, MSG_ERROR_BROADCAST_INSTRUCTION,
    MSG_ERROR_BROADCAST_RESTART, MSG_ERROR_CALLBACK_UNSUPPORTED, MSG_HELP,
    MSG_LINKS, MSG_LINK_ALREADY_REVOKED, MSG_LINK_NOT_FOUND,
    MSG_LINK_NOT_OWNER, MSG_LINK_REGENERATED_ALERT, MSG_LINK_REVOKED_ALERT,
    MSG_LINK_REVOKED_NOTE
)
from Thunder.vars import Var

async def get_force_channel_button(client: Client):
    if not Var.FORCE_CHANNEL_ID:
        return None
    try:
        try:
            chat = await client.get_chat(Var.FORCE_CHANNEL_ID)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            chat = await client.get_chat(Var.FORCE_CHANNEL_ID)
        if chat:
            invite_link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)
            if invite_link:
                return [InlineKeyboardButton(
                    MSG_BUTTON_JOIN_CHANNEL.format(channel_title=chat.title or "Channel"),
                    url=invite_link
                )]
    except Exception as e:
        logger.error(f"Error getting force channel button: {e}", exc_info=True)
    return None

@StreamBot.on_callback_query(filters.regex(r"^help_command$"))
async def help_callback(client: Client, callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        buttons = [[InlineKeyboardButton(MSG_BUTTON_ABOUT, callback_data="about_command")]]
        force_button = await get_force_channel_button(client)
        if force_button:
            buttons.append(force_button)
        buttons.append([InlineKeyboardButton(MSG_BUTTON_CLOSE, callback_data="close_panel")])
        try:
            await callback_query.message.edit_text(
                text=MSG_HELP.format(max_files=Var.MAX_BATCH_FILES),
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await callback_query.message.edit_text(
                text=MSG_HELP.format(max_files=Var.MAX_BATCH_FILES),
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f"Error in help callback: {e}", exc_info=True)
        try:
            await callback_query.answer("An error occurred. Please try again.", show_alert=True)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await callback_query.answer("An error occurred. Please try again.", show_alert=True)

@StreamBot.on_callback_query(filters.regex(r"^about_command$"))
async def about_callback(client: Client, callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        buttons = [
            [InlineKeyboardButton(MSG_BUTTON_GET_HELP, callback_data="help_command")],
            [
                InlineKeyboardButton(MSG_BUTTON_GITHUB, url="https://github.com/fyaz05/FileToLink"),
                InlineKeyboardButton(MSG_BUTTON_CLOSE, callback_data="close_panel")
            ]
        ]
        try:
            await callback_query.message.edit_text(
                text=MSG_ABOUT,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await callback_query.message.edit_text(
                text=MSG_ABOUT,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f"Error in about callback: {e}", exc_info=True)
        try:
            await callback_query.answer("An error occurred. Please try again.", show_alert=True)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await callback_query.answer("An error occurred. Please try again.", show_alert=True)

@StreamBot.on_callback_query(filters.regex(r"^restart_broadcast$"))
async def restart_broadcast_callback(client: Client, callback_query: CallbackQuery):
    if not await owner_only(client, callback_query):
        return
    try:
        try:
            await callback_query.answer(MSG_ERROR_BROADCAST_RESTART, show_alert=True)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await callback_query.answer(MSG_ERROR_BROADCAST_RESTART, show_alert=True)
        buttons = [
            [
                InlineKeyboardButton(MSG_BUTTON_GET_HELP, callback_data="help_command"),
                InlineKeyboardButton(MSG_BUTTON_CLOSE, callback_data="close_panel")
            ]
        ]
        try:
            await callback_query.message.edit_text(
                MSG_ERROR_BROADCAST_INSTRUCTION,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await callback_query.message.edit_text(
                MSG_ERROR_BROADCAST_INSTRUCTION,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"Error in restart broadcast callback: {e}", exc_info=True)
        try:
            await callback_query.answer("An error occurred. Please try again.", show_alert=True)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await callback_query.answer("An error occurred. Please try again.", show_alert=True)

@StreamBot.on_callback_query(filters.regex(r"^close_panel$"))
async def close_panel_callback(client: Client, callback_query: CallbackQuery):
    try:
        try:
            await callback_query.answer()
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await callback_query.answer()
        try:
            try:
                await callback_query.message.delete()
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await callback_query.message.delete()
        except MessageDeleteForbidden:
            logger.debug(f"Failed to delete callback query message due to permissions. Message ID: {callback_query.message.id}")
        except Exception as e:
            logger.error(f"Error deleting callback query message: {e}", exc_info=True)

        if callback_query.message.reply_to_message:
            try:
                reply_msg = callback_query.message.reply_to_message
                try:
                    await reply_msg.delete()
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    await reply_msg.delete()
            except MessageDeleteForbidden:
                logger.debug(f"Failed to delete replied message due to permissions. Message ID: {reply_msg.id}")
            except Exception as e:
                logger.error(f"Error deleting replied message: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"General error in close panel callback: {e}", exc_info=True)

@StreamBot.on_callback_query(filters.regex(r"^cancel_"))
async def cancel_broadcast(client: Client, callback_query: CallbackQuery):
    try:
        broadcast_id = callback_query.data.split("_")[1]
        if broadcast_id in broadcast_ids:
            broadcast_ids[broadcast_id]["cancelled"] = True
            try:
                await callback_query.message.edit_text(
                    MSG_BROADCAST_CANCEL.format(broadcast_id=broadcast_id)
                )
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await callback_query.message.edit_text(
                    MSG_BROADCAST_CANCEL.format(broadcast_id=broadcast_id)
                )
        else:
            try:
                await callback_query.answer(
                    MSG_BROADCAST_CANCEL.format(broadcast_id=broadcast_id),
                    show_alert=True
                )
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await callback_query.answer(
                    MSG_BROADCAST_CANCEL.format(broadcast_id=broadcast_id),
                    show_alert=True
                )
    except Exception as e:
        logger.error(f"Error in cancel broadcast callback: {e}", exc_info=True)
        try:
            await callback_query.answer("An error occurred. Please try again.", show_alert=True)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await callback_query.answer("An error occurred. Please try again.", show_alert=True)

def _is_link_owner(callback_query: CallbackQuery, record) -> bool:
    user = callback_query.from_user
    if not user:
        return False
    if user.id == Var.OWNER_ID:
        return True
    return user.id == record.get("first_source_chat_id")


async def _safe_answer(callback_query: CallbackQuery, text: str, *, show_alert: bool = False) -> None:
    try:
        await callback_query.answer(text, show_alert=show_alert)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            await callback_query.answer(text, show_alert=show_alert)
        except Exception:
            pass
    except Exception:
        pass


async def _safe_edit_text(message, text: str, reply_markup) -> None:
    try:
        await message.edit_text(
            text,
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.edit_text(
            text,
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
    except MessageNotModified:
        pass


def _revoked_markup(file_unique_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(
        MSG_BUTTON_REGENERATE_LINK, callback_data=f"regen_{file_unique_id}")]])


async def _show_revoked_state(callback_query: CallbackQuery, record) -> None:
    text = callback_query.message.text or ""
    if MSG_LINK_REVOKED_NOTE.strip() not in text:
        text = text + MSG_LINK_REVOKED_NOTE
    await _safe_edit_text(
        callback_query.message, text, _revoked_markup(record["file_unique_id"]))


async def _show_regenerated_state(callback_query: CallbackQuery, record, old_links, new_links) -> None:
    text = callback_query.message.text or ""
    text = text.replace(old_links["stream_link"], new_links["stream_link"])
    text = text.replace(old_links["online_link"], new_links["online_link"])
    text = text.replace(MSG_LINK_REVOKED_NOTE, "")
    if new_links["stream_link"] not in text:
        text = MSG_LINKS.format(
            file_name=new_links['media_name'],
            file_size=new_links['media_size'],
            download_link=new_links['online_link'],
            stream_link=new_links['stream_link']
        )
    await _safe_edit_text(
        callback_query.message, text,
        get_link_buttons(new_links, record["file_unique_id"]))


@StreamBot.on_callback_query(filters.regex(r"^revoke_[A-Za-z0-9_-]+$"))
async def revoke_link_callback(client: Client, callback_query: CallbackQuery):
    try:
        file_unique_id = callback_query.data.split("_", 1)[1]
        record = await get_file_by_unique_id(file_unique_id)
        if not record:
            await _safe_answer(callback_query, MSG_LINK_NOT_FOUND, show_alert=True)
            return
        if not _is_link_owner(callback_query, record):
            await _safe_answer(callback_query, MSG_LINK_NOT_OWNER, show_alert=True)
            return
        if not is_link_active(record):
            await _safe_answer(callback_query, MSG_LINK_ALREADY_REVOKED, show_alert=True)
            await _show_revoked_state(callback_query, record)
            return
        record = await revoke_canonical_file(record)
        await _show_revoked_state(callback_query, record)
        await _safe_answer(callback_query, MSG_LINK_REVOKED_ALERT)
    except Exception as e:
        logger.error(f"Error in revoke link callback: {e}", exc_info=True)
        await _safe_answer(callback_query, "An error occurred. Please try again.", show_alert=True)


@StreamBot.on_callback_query(filters.regex(r"^regen_[A-Za-z0-9_-]+$"))
async def regenerate_link_callback(client: Client, callback_query: CallbackQuery):
    try:
        file_unique_id = callback_query.data.split("_", 1)[1]
        record = await get_file_by_unique_id(file_unique_id)
        if not record:
            await _safe_answer(callback_query, MSG_LINK_NOT_FOUND, show_alert=True)
            return
        if not _is_link_owner(callback_query, record):
            await _safe_answer(callback_query, MSG_LINK_NOT_OWNER, show_alert=True)
            return
        # get_shortener_status only reads .from_user, so a CallbackQuery works here.
        shortener = await get_shortener_status(client, callback_query)
        old_links = await gen_canonical_links(
            file_name=record["file_name"],
            file_size=int(record.get("file_size", 0) or 0),
            public_hash=record["public_hash"],
            shortener=shortener
        )
        record = await regenerate_canonical_link(record)
        new_links = await gen_canonical_links(
            file_name=record["file_name"],
            file_size=int(record.get("file_size", 0) or 0),
            public_hash=record["public_hash"],
            shortener=shortener
        )
        await _show_regenerated_state(callback_query, record, old_links, new_links)
        await _safe_answer(callback_query, MSG_LINK_REGENERATED_ALERT)
    except Exception as e:
        logger.error(f"Error in regenerate link callback: {e}", exc_info=True)
        await _safe_answer(callback_query, "An error occurred. Please try again.", show_alert=True)


@StreamBot.on_callback_query()
async def fallback_callback(client: Client, callback_query: CallbackQuery):
    try:
        try:
            await callback_query.answer(MSG_ERROR_CALLBACK_UNSUPPORTED, show_alert=True)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await callback_query.answer(MSG_ERROR_CALLBACK_UNSUPPORTED, show_alert=True)
    except Exception as e:
        logger.error(f"Error in fallback callback: {e}", exc_info=True)
