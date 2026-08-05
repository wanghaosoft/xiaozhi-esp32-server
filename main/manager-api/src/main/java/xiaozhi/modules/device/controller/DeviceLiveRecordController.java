package xiaozhi.modules.device.controller;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.device.dto.ExternalLiveCommandRecordDTO;
import xiaozhi.modules.device.dto.ExternalLiveEventRecordDTO;
import xiaozhi.modules.device.entity.LiveCommandRecordEntity;
import xiaozhi.modules.device.entity.LiveEventRecordEntity;
import xiaozhi.modules.device.service.LiveRecordService;

@Tag(name = "直播中控记录")
@RestController
@RequiredArgsConstructor
@RequestMapping("/device/external/live-records")
public class DeviceLiveRecordController {
    private final LiveRecordService liveRecordService;

    @PostMapping("/events")
    @Operation(summary = "外部系统上报直播事件记录")
    public Result<Boolean> reportEvent(@Valid @RequestBody ExternalLiveEventRecordDTO request) {
        liveRecordService.reportEvent(request);
        return new Result<Boolean>().ok(true);
    }

    @PostMapping("/commands")
    @Operation(summary = "外部系统上报直播命令记录")
    public Result<Boolean> reportCommand(@Valid @RequestBody ExternalLiveCommandRecordDTO request) {
        liveRecordService.reportCommand(request);
        return new Result<Boolean>().ok(true);
    }

    @GetMapping("/events")
    @Operation(summary = "查看最近直播事件记录")
    public Result<List<LiveEventRecordEntity>> listEvents(@RequestParam(defaultValue = "20") int limit) {
        return new Result<List<LiveEventRecordEntity>>().ok(liveRecordService.listEventRecords(limit));
    }

    @GetMapping("/commands")
    @Operation(summary = "查看最近直播命令记录")
    public Result<List<LiveCommandRecordEntity>> listCommands(@RequestParam(defaultValue = "20") int limit) {
        return new Result<List<LiveCommandRecordEntity>>().ok(liveRecordService.listCommandRecords(limit));
    }
}