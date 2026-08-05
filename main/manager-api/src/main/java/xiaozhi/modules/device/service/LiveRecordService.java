package xiaozhi.modules.device.service;

import java.util.List;

import xiaozhi.modules.device.dto.ExternalLiveCommandRecordDTO;
import xiaozhi.modules.device.dto.ExternalLiveEventRecordDTO;
import xiaozhi.modules.device.entity.LiveCommandRecordEntity;
import xiaozhi.modules.device.entity.LiveEventRecordEntity;

public interface LiveRecordService {
    void reportEvent(ExternalLiveEventRecordDTO request);

    void reportCommand(ExternalLiveCommandRecordDTO request);

    List<LiveEventRecordEntity> listEventRecords(int limit);

    List<LiveCommandRecordEntity> listCommandRecords(int limit);
}