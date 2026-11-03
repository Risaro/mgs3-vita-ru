#include <psp2/kernel/modulemgr.h>
#include <taihen.h>
#include "strings.h"
#include "relocs.h"

#define SEG0_LINK 0x81000000u
#define SEG1_LINK 0x8199E000u
#define FONT_FN 0x81681DF0u
#define GAME_MALLOC 0x818ADBC4u
#define FONT_PTR 0x81B17E80u
#define FONT_STATE 0x81B17E7Cu

__asm__(".section .rodata\n.balign 4\n.global font_raw\nfont_raw:\n.incbin \"font.raw\"\n.global font_raw_end\nfont_raw_end:\n.text\n");
extern const uint8_t font_raw[];
extern const uint8_t font_raw_end[];

int _start(SceSize args, void *argp) __attribute__((weak, alias("module_start")));

static tai_hook_ref_t hook_ref;
static SceUID hook_id = -1;
static uint32_t d0, d1;

static uint32_t font_load_hook(void) {
    void *(*game_malloc)(uint32_t) = (void *(*)(uint32_t))(GAME_MALLOC + d0);
    uint32_t size = (uint32_t)(font_raw_end - font_raw);
    uint8_t *buf = game_malloc(size);
    if (!buf)
        return TAI_CONTINUE(uint32_t, hook_ref);
    for (uint32_t i = 0; i < size; i++)
        buf[i] = font_raw[i];
    for (uint32_t r = 0; r < RELOC_COUNT; r++)
        *(volatile uint32_t *)(relocs[r].va + d1) = (uint32_t)relocs[r].str;
    *(volatile uint32_t *)(FONT_PTR + d1) = (uint32_t)buf;
    *(volatile uint32_t *)(FONT_STATE + d1) = 3;
    return FONT_STATE + d1;
}

int module_start(SceSize args, void *argp) {
    tai_module_info_t info;
    info.size = sizeof(info);
    if (taiGetModuleInfo(TAI_MAIN_MODULE, &info) < 0)
        return SCE_KERNEL_START_SUCCESS;
    SceKernelModuleInfo mi;
    mi.size = sizeof(mi);
    if (sceKernelGetModuleInfo(info.modid, &mi) < 0)
        return SCE_KERNEL_START_SUCCESS;
    d0 = (uint32_t)mi.segments[0].vaddr - SEG0_LINK;
    d1 = (uint32_t)mi.segments[1].vaddr - SEG1_LINK;
    volatile uint16_t *fn = (volatile uint16_t *)(FONT_FN + d0);
    if (fn[0] != 0xB570 || fn[2] != 0xF247 || fn[3] != 0x5058 || fn[4] != 0xF2C8 || fn[5] != 0x10A6)
        return SCE_KERNEL_START_SUCCESS;
    for (uint32_t i = 0; i < STR_PATCH_COUNT; i++)
        taiInjectData(info.modid, 0, str_patches[i].off, str_patches[i].data, str_patches[i].size);
    hook_id = taiHookFunctionOffset(&hook_ref, info.modid, 0, FONT_FN - SEG0_LINK, 1, font_load_hook);
    return SCE_KERNEL_START_SUCCESS;
}

int module_stop(SceSize args, void *argp) {
    if (hook_id >= 0)
        taiHookRelease(hook_id, hook_ref);
    return SCE_KERNEL_STOP_SUCCESS;
}
